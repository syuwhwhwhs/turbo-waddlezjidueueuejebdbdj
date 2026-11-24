import json, hmac, hashlib, time, os, uuid
from pathlib import Path
from urllib.parse import parse_qsl
from fastapi import FastAPI, Header, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from PIL import Image
import httpx
import subprocess, math
from app.config import BOT_TOKEN, ADMIN_IDS, WORK_DIR
from app.db import init, save, db

app=FastAPI(title='Taha Emoji Studio', version='2.0.0')
os.makedirs(WORK_DIR,exist_ok=True)
app.mount('/static',StaticFiles(directory='app/static'),name='static')
UPLOAD_DIR=Path(WORK_DIR)/'uploads'; UPLOAD_DIR.mkdir(parents=True,exist_ok=True)
PREVIEW_DIR=Path(WORK_DIR)/'previews'; PREVIEW_DIR.mkdir(parents=True,exist_ok=True)

def auth(raw):
    if not BOT_TOKEN or not raw: raise HTTPException(401,'Open inside Telegram')
    d=dict(parse_qsl(raw,keep_blank_values=True)); got=d.pop('hash',None)
    check='\n'.join(f'{k}={v}' for k,v in sorted(d.items()))
    secret=hmac.new(b'WebAppData',BOT_TOKEN.encode(),hashlib.sha256).digest()
    calc=hmac.new(secret,check.encode(),hashlib.sha256).hexdigest()
    if not got or not hmac.compare_digest(calc,got): raise HTTPException(401,'Invalid Telegram signature')
    try: age=time.time()-int(d.get('auth_date','0'))
    except ValueError: raise HTTPException(401,'Invalid auth date')
    if age < -60 or age > 86400: raise HTTPException(401,'Session expired')
    try: u=json.loads(d.get('user','{}'))
    except json.JSONDecodeError: raise HTTPException(401,'Invalid Telegram user')
    if not u.get('id'): raise HTTPException(401,'Missing Telegram user')
    lang=save(u['id'],name=u.get('first_name',''),username=u.get('username',''))
    return u,lang

@app.on_event('startup')
def startup(): init()

@app.get('/')
def index(): return FileResponse('app/static/index.html')

@app.get('/api/me')
def me(x_telegram_init_data:str=Header(default='')):
    u,l=auth(x_telegram_init_data)
    with db() as c:
        jobs=c.execute('SELECT COUNT(*) n FROM jobs WHERE user_id=?',(u['id'],)).fetchone()['n']
    return {'id':u['id'],'name':u.get('first_name',''),'username':u.get('username',''),
            'language':l,'admin':u['id'] in ADMIN_IDS,'jobs':jobs}

class Lang(BaseModel): language:str
@app.post('/api/language')
def language(b:Lang,x_telegram_init_data:str=Header(default='')):
    if b.language not in ('fa','en'): raise HTTPException(400,'Unsupported language')
    u,_=auth(x_telegram_init_data)
    save(u['id'],b.language,u.get('first_name',''),u.get('username',''))
    return {'ok':True,'language':b.language}

async def fetch_sticker(emoji_id):
    async with httpx.AsyncClient(timeout=25) as c:
        r=await c.post(f'https://api.telegram.org/bot{BOT_TOKEN}/getCustomEmojiStickers',json={'custom_emoji_ids':[emoji_id]})
        r.raise_for_status(); j=r.json()
    if not j.get('ok') or not j.get('result'): raise HTTPException(404,'Emoji not found')
    s=j['result'][0]
    fmt='TGS' if s.get('is_animated') else 'WEBM' if s.get('is_video') else 'WEBP'
    return s,fmt

class Lookup(BaseModel): emoji_id:str=Field(min_length=1,max_length=40)
@app.post('/api/emoji/lookup')
async def lookup(b:Lookup,x_telegram_init_data:str=Header(default='')):
    auth(x_telegram_init_data)
    if not b.emoji_id.isdigit(): raise HTTPException(400,'Invalid ID')
    s,fmt=await fetch_sticker(b.emoji_id)
    return {'found':True,'emoji_id':b.emoji_id,'file_id':s.get('file_id'),
            'emoji':s.get('emoji'),'set_name':s.get('set_name'),'format':fmt,
            'preview_url':f'/api/emoji/preview/{b.emoji_id}'}

@app.get('/api/emoji/preview/{emoji_id}')
async def emoji_preview(emoji_id:str, x_telegram_init_data:str=Header(default='')):
    # Preview files are cached server-side; the bot token is never exposed to the browser.
    auth(x_telegram_init_data)
    if not emoji_id.isdigit(): raise HTTPException(400,'Invalid ID')
    cached=[PREVIEW_DIR/(emoji_id+'.webm'), PREVIEW_DIR/(emoji_id+'.webp')]
    cached=[p for p in cached if p.is_file()]
    if cached:
        return FileResponse(cached[0], media_type={'webp':'image/webp','webm':'video/webm'}.get(cached[0].suffix.lstrip('.'),'application/octet-stream'))
    sticker,fmt=await fetch_sticker(emoji_id)
    async with httpx.AsyncClient(timeout=30) as client:
        fr=await client.post(f'https://api.telegram.org/bot{BOT_TOKEN}/getFile',json={'file_id':sticker['file_id']})
        fj=fr.json()
        if not fj.get('ok'): raise HTTPException(502,'Telegram file lookup failed')
        file_path=fj['result']['file_path']
        download=await client.get(f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}')
        if download.status_code!=200: raise HTTPException(502,'Could not download preview')
        raw=download.content
    if fmt=='WEBM':
        dest=PREVIEW_DIR/(emoji_id+'.webm'); dest.write_bytes(raw)
        return FileResponse(dest,media_type='video/webm')
    if fmt=='WEBP':
        dest=PREVIEW_DIR/(emoji_id+'.webp'); dest.write_bytes(raw)
        return FileResponse(dest,media_type='image/webp')
    # Convert TGS/Lottie to a small animated WebP preview. This is cached after first request.
    try:
        from rlottie_python import LottieAnimation
        import tempfile
        src=PREVIEW_DIR/(emoji_id+'.tgs'); src.write_bytes(raw)
        anim=LottieAnimation.from_tgs(str(src))
        total=max(1,int(anim.lottie_animation_get_totalframe()))
        fps=float(anim.lottie_animation_get_framerate() or 30)
        duration=min(2.0,float(anim.lottie_animation_get_duration() or total/fps))
        count=max(2,min(48,int(duration*24)))
        frames=[]
        for i in range(count):
            frame_no=min(total-1,int(i*fps/24))
            im=anim.render_pillow_frame(frame_num=frame_no).convert('RGBA').resize((100,100))
            frames.append(im)
        dest=PREVIEW_DIR/(emoji_id+'.webp')
        frames[0].save(dest,'WEBP',save_all=True,append_images=frames[1:],duration=round(1000/24),loop=0,lossless=False,quality=78,method=4)
        return FileResponse(dest,media_type='image/webp')
    except Exception as e:
        raise HTTPException(503,'TGS preview renderer unavailable: '+str(e)[:160])

@app.post('/api/upload-logo')
async def upload_logo(file:UploadFile=File(...),x_telegram_init_data:str=Header(default='')):
    auth(x_telegram_init_data)
    if file.content_type not in ('image/png','image/jpeg','image/webp'):
        raise HTTPException(415,'Upload PNG, JPG or WEBP image')
    data=await file.read(5*1024*1024+1)
    if len(data)>5*1024*1024: raise HTTPException(413,'Image must be 5 MB or smaller')
    ext={'image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp'}[file.content_type]
    path=UPLOAD_DIR/(uuid.uuid4().hex+ext)
    try:
        from io import BytesIO
        im=Image.open(BytesIO(data))
        if im.width>2048 or im.height>2048: raise ValueError('Image dimensions are too large')
        im.verify()
    except Exception: raise HTTPException(400,'Invalid image file')
    path.write_bytes(data)
    return {'upload_id':path.name,'preview_url':'/api/uploads/'+path.name}

@app.get('/api/uploads/{name}')
def get_upload(name:str,x_telegram_init_data:str=Header(default='')):
    auth(x_telegram_init_data)
    if Path(name).name!=name: raise HTTPException(400,'Invalid name')
    p=UPLOAD_DIR/name
    if not p.is_file(): raise HTTPException(404,'Upload not found')
    return FileResponse(p)

class Job(BaseModel):
    emoji_id:str=Field(min_length=1,max_length=40)
    mode:str
    replacement:str=Field(default='',max_length=100)
    upload_id:str|None=None
@app.post('/api/jobs')
async def job(b:Job,x_telegram_init_data:str=Header(default='')):
    u,_=auth(x_telegram_init_data)
    if not b.emoji_id.isdigit() or b.mode not in ('text','logo'):
        raise HTTPException(400,'Invalid input')
    if b.mode=='text' and not b.replacement.strip(): raise HTTPException(400,'Text is required')
    if b.mode=='logo':
        if not b.upload_id or Path(b.upload_id).name!=b.upload_id or not (UPLOAD_DIR/b.upload_id).is_file():
            raise HTTPException(400,'Upload a logo first')
        replacement=str(UPLOAD_DIR/b.upload_id)
    sticker,fmt=await fetch_sticker(b.emoji_id)
    with db() as c:
        cur=c.execute('''INSERT INTO jobs(user_id,emoji_id,mode,replacement,source_file_id,source_format,status)
          VALUES(?,?,?,?,?,?,?)''',(u['id'],b.emoji_id,b.mode,b.replacement if b.mode=='text' else replacement,
          sticker['file_id'],fmt,'queued'))
        jid=cur.lastrowid
    return {'ok':True,'job_id':jid,'status':'queued','format':fmt}

@app.get('/api/packs')
def packs(x_telegram_init_data:str=Header(default='')):
    u,_=auth(x_telegram_init_data)
    with db() as c:
        rows=c.execute('SELECT id,emoji_id,source_format,status,pack_name,created_at FROM jobs WHERE user_id=? ORDER BY id DESC LIMIT 50',(u['id'],)).fetchall()
    return {'items':[dict(x) for x in rows]}

@app.get('/api/admin/stats')
def stats(x_telegram_init_data:str=Header(default='')):
    u,_=auth(x_telegram_init_data)
    if u['id'] not in ADMIN_IDS: raise HTTPException(403,'Admin only')
    with db() as c:
        return {'users':c.execute('SELECT COUNT(*) n FROM users').fetchone()['n'],
                'jobs':c.execute('SELECT COUNT(*) n FROM jobs').fetchone()['n'],
                'failed':c.execute("SELECT COUNT(*) n FROM jobs WHERE status='failed'").fetchone()['n']}
