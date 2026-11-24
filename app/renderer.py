import os, subprocess, tempfile, math
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import httpx

FONT_CANDIDATES=(
 '/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf',
 '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
 '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf')

def _font(size):
    for p in FONT_CANDIDATES:
        if os.path.exists(p): return ImageFont.truetype(p,size)
    return ImageFont.load_default()

async def _load_logo(source):
    if source.startswith('https://'):
        async with httpx.AsyncClient(timeout=20,follow_redirects=True) as client:
            r=await client.get(source); r.raise_for_status(); data=r.content
    else:
        p=Path(source)
        if not p.is_file(): raise ValueError('Uploaded logo file was not found')
        data=p.read_bytes()
    try: return Image.open(BytesIO(data)).convert('RGBA')
    except Exception as e: raise ValueError('Logo must be a valid PNG, JPG or WEBP image') from e

def make_overlay(mode,replacement,size=(100,100)):
    w,h=size
    canvas=Image.new('RGBA',(w,h),(0,0,0,0))
    if mode=='text':
        draw=ImageDraw.Draw(canvas)
        txt=replacement.strip()[:24]
        font_size=max(12,int(min(w,h)*.22))
        font=_font(font_size)
        kwargs={}
        # Use complex-script shaping when Pillow is built with libraqm.
        try:
            bbox=draw.textbbox((0,0),txt,font=font,stroke_width=max(1,w//100),direction='rtl',language='fa')
            kwargs={'direction':'rtl','language':'fa'}
        except Exception:
            bbox=draw.textbbox((0,0),txt,font=font,stroke_width=max(1,w//100))
        while font_size>8 and bbox[2]-bbox[0] > w*.9:
            font_size-=1; font=_font(font_size)
            try: bbox=draw.textbbox((0,0),txt,font=font,stroke_width=max(1,w//100),**kwargs)
            except Exception: bbox=draw.textbbox((0,0),txt,font=font,stroke_width=max(1,w//100))
        x=(w-(bbox[2]-bbox[0]))/2-bbox[0]
        y=(h-(bbox[3]-bbox[1]))/2-bbox[1]
        try: draw.text((x,y),txt,font=font,fill='white',stroke_width=max(1,w//100),stroke_fill='#5420a8',**kwargs)
        except Exception: draw.text((x,y),txt,font=font,fill='white',stroke_width=max(1,w//100),stroke_fill='#5420a8')
    elif mode=='logo':
        raise RuntimeError('Use make_overlay_async for logo rendering')
    return canvas

async def make_overlay_async(mode,replacement,size=(100,100)):
    if mode=='text': return make_overlay(mode,replacement,size)
    if mode=='logo':
        logo=await _load_logo(replacement)
        logo.thumbnail((int(size[0]*.48),int(size[1]*.48)),Image.Resampling.LANCZOS)
        canvas=Image.new('RGBA',size,(0,0,0,0))
        canvas.alpha_composite(logo,((size[0]-logo.width)//2,(size[1]-logo.height)//2))
        return canvas
    raise ValueError('Unknown edit mode')

async def render(source_path,fmt,mode,replacement,out_path):
    os.makedirs(os.path.dirname(out_path),exist_ok=True)
    if fmt=='TGS':
        # Render the original Lottie/TGS frames with rlottie, overlay the edit on
        # every frame, then encode a Telegram-compatible 100x100 VP9 WEBM.
        try:
            from rlottie_python import LottieAnimation
        except ImportError as e:
            raise RuntimeError('برای پردازش TGS باید rlottie-python نصب باشد.') from e
        anim=LottieAnimation.from_tgs(source_path)
        total=max(1,int(anim.lottie_animation_get_totalframe()))
        source_fps=float(anim.lottie_animation_get_framerate() or 60)
        duration=float(anim.lottie_animation_get_duration() or (total/source_fps))
        if duration<=0: duration=total/source_fps
        duration=min(duration,3.0)
        frame_count=max(1,min(90,int(math.ceil(duration*30))))
        overlay=await make_overlay_async(mode,replacement,(100,100))
        with tempfile.TemporaryDirectory(prefix='tgs_frames_') as td:
            for i in range(frame_count):
                frame_no=min(total-1,int(round(i*source_fps/30)))
                frame=anim.render_pillow_frame(frame_num=frame_no).convert('RGBA')
                frame=frame.resize((100,100),Image.Resampling.LANCZOS)
                frame.alpha_composite(overlay)
                frame.save(os.path.join(td,f'frame_{i:04d}.png'))
            # Keep within Telegram's video custom-emoji size limit where possible.
            encoded=False
            for crf in (32,38,44,50):
                cmd=['ffmpeg','-v','error','-y','-framerate','30','-i',os.path.join(td,'frame_%04d.png'),
                     '-an','-frames:v',str(frame_count),'-c:v','libvpx-vp9','-pix_fmt','yuva420p',
                     '-auto-alt-ref','0','-b:v','0','-crf',str(crf),out_path]
                p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                if p.returncode==0 and os.path.exists(out_path) and os.path.getsize(out_path)<=256*1024:
                    encoded=True; break
            if not encoded:
                if p.returncode: raise RuntimeError(p.stderr.decode(errors='ignore')[-1000:])
                raise RuntimeError('حجم خروجی از سقف 256KB ایموجی ویدیویی تلگرام بیشتر است؛ لوگو/متن ساده‌تری انتخاب کن.')
        return out_path
    if fmt=='WEBP':
        base=Image.open(source_path).convert('RGBA')
        base=base.resize((100,100),Image.Resampling.LANCZOS)
        size=(100,100)
        overlay=await make_overlay_async(mode,replacement,size)
        base.alpha_composite(overlay)
        base.save(out_path,'WEBP',lossless=True,method=6)
        return out_path
    if fmt=='WEBM':
        # Telegram video stickers are square transparent VP9 WebM. Preserve the source canvas.
        probe=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height','-of','csv=s=x:p=0',source_path],capture_output=True,text=True)
        if probe.returncode: raise RuntimeError('Could not inspect source WebM; install ffmpeg.')
        try: width,height=map(int,probe.stdout.strip().split('x'))
        except Exception: width=height=512
        overlay=await make_overlay_async(mode,replacement,(100,100))
        ov=out_path+'.overlay.png'; overlay.save(ov)
        p=None
        for crf in (32,38,44,50):
            cmd=['ffmpeg','-v','error','-y','-i',source_path,'-i',ov,
                 '-filter_complex','[0:v]scale=100:100:flags=lanczos[base];[base][1:v]overlay=0:0:format=auto:eof_action=repeat',
                 '-an','-t','3','-r','30','-c:v','libvpx-vp9','-pix_fmt','yuva420p','-auto-alt-ref','0','-b:v','0','-crf',str(crf),out_path]
            p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            if p.returncode==0 and os.path.exists(out_path) and os.path.getsize(out_path)<=256*1024: break
        try: os.remove(ov)
        except OSError: pass
        if p.returncode: raise RuntimeError(p.stderr.decode(errors='ignore')[-1200:])
        if not os.path.exists(out_path) or os.path.getsize(out_path)>256*1024:
            raise RuntimeError('حجم خروجی از سقف 256KB ایموجی ویدیویی تلگرام بیشتر است.')
        return out_path
    raise ValueError('Unsupported sticker format')
