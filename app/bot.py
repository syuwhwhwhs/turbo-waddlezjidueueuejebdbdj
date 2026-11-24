import asyncio
from pathlib import Path
from aiogram import Bot,Dispatcher,F
from aiogram.filters import CommandStart,Command
from aiogram.types import Message,CallbackQuery,InlineKeyboardMarkup,InlineKeyboardButton,WebAppInfo,FSInputFile
from app.config import BOT_TOKEN,WEBAPP_URL,BOT_USERNAME,ADMIN_IDS,WORK_DIR
from app.db import init,save,user,db,get_job,get_user_pack,save_user_pack
from app.i18n import t
from app.renderer import render
import httpx
if not BOT_TOKEN:
    raise RuntimeError('Set BOT_TOKEN in .env before starting the bot')
bot=Bot(BOT_TOKEN); dp=Dispatcher()
def lang_of(uid):
    u=user(uid); return u['language'] if u else 'fa'
@dp.message(CommandStart())
async def start(m:Message):
    u=m.from_user; old=user(u.id)
    if not old:
        kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🇮🇷 فارسی',callback_data='lang:fa'),InlineKeyboardButton(text='🇬🇧 English',callback_data='lang:en')]])
        await m.answer(t('fa','choose'),reply_markup=kb); return
    await home(m,old['language'])
async def home(m,lang,user_id=None):
    user_id = user_id if user_id is not None else m.from_user.id
    rows=[]
    if WEBAPP_URL: rows.append([InlineKeyboardButton(text=t(lang,'open'),web_app=WebAppInfo(url=WEBAPP_URL))])
    else: rows.append([InlineKeyboardButton(text=t(lang,'need'),callback_data='noop')])
    rows.append([InlineKeyboardButton(text='🌐 فارسی / English',callback_data='change')])
    if user_id in ADMIN_IDS: rows.append([InlineKeyboardButton(text=t(lang,'admin'),callback_data='admin')])
    await m.answer(t(lang,'welcome')+'\n'+t(lang,'help'),reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
@dp.callback_query(F.data.startswith('lang:'))
async def language(c:CallbackQuery):
    lang=c.data.split(':')[1]; u=c.from_user
    save(u.id,lang,u.first_name or '',u.username or '')
    await c.answer(t(lang,'saved')); await c.message.edit_reply_markup(reply_markup=None); await home(c.message,lang,c.from_user.id)
@dp.callback_query(F.data=='change')
async def change(c:CallbackQuery):
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🇮🇷 فارسی',callback_data='lang:fa'),InlineKeyboardButton(text='🇬🇧 English',callback_data='lang:en')]])
    await c.message.answer(t(lang_of(c.from_user.id),'choose'),reply_markup=kb); await c.answer()
@dp.callback_query(F.data=='admin')
async def admin(c:CallbackQuery):
    if c.from_user.id not in ADMIN_IDS: return await c.answer('Forbidden',show_alert=True)
    with db() as con:
        n=con.execute('SELECT COUNT(*) n FROM users').fetchone()['n']; j=con.execute('SELECT COUNT(*) n FROM jobs').fetchone()['n']
    await c.message.answer(t(lang_of(c.from_user.id),'stats',users=n,jobs=j)); await c.answer()
@dp.message(Command('help'))
async def help_cmd(m:Message): await m.answer(t(lang_of(m.from_user.id),'help'))
@dp.message(Command('language'))
async def lang_cmd(m:Message): await change_fake(m)
async def change_fake(m):
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🇮🇷 فارسی',callback_data='lang:fa'),InlineKeyboardButton(text='🇬🇧 English',callback_data='lang:en')]])
    await m.answer(t(lang_of(m.from_user.id),'choose'),reply_markup=kb)
async def download_file(file_id,dest):
    f=await bot.get_file(file_id)
    await bot.download_file(f.file_path,destination=dest)
async def process_job(job):
    jid=job['id']; uid=job['user_id']; lang=lang_of(uid)
    work=Path(WORK_DIR)/str(jid); work.mkdir(parents=True,exist_ok=True)
    try:
        source=work/('source.'+job['source_format'].lower())
        await download_file(job['source_file_id'],str(source))
        output_format='WEBM' if job['source_format'] in ('WEBM','TGS') else 'WEBP'
        out=work/('result.'+('webm' if output_format=='WEBM' else 'webp'))
        await render(str(source),job['source_format'],job['mode'],job['replacement'],str(out))
        with db() as c: c.execute("UPDATE jobs SET status='ready',result_path=?,source_format=? WHERE id=?",(str(out),output_format,jid))
        await bot.send_sticker(uid,FSInputFile(out))
        kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(lang,'yes'),callback_data=f'pack:{jid}'),InlineKeyboardButton(text=t(lang,'no'),callback_data=f'keep:{jid}')]])
        await bot.send_message(uid,t(lang,'askpack'),reply_markup=kb)
    except Exception as e:
        with db() as c: c.execute("UPDATE jobs SET status='failed' WHERE id=?",(jid,))
        await bot.send_message(uid,t(lang,'failed')+'\n'+str(e)[:300])
@dp.callback_query(F.data.startswith('keep:'))
async def keep(c:CallbackQuery):
    try:
        jid=int(c.data.split(':')[1]); job=get_job(jid)
        if not job or job['user_id']!=c.from_user.id: return await c.answer('Not yours',show_alert=True)
    except Exception: return await c.answer('Invalid request',show_alert=True)
    await c.message.edit_reply_markup(reply_markup=None); await c.answer('OK')
@dp.callback_query(F.data.startswith('pack:'))
async def add_pack(c:CallbackQuery):
    jid=int(c.data.split(':')[1]); job=get_job(jid)
    if not job or job['user_id']!=c.from_user.id or job['status']!='ready':
        return await c.answer('Not available',show_alert=True)
    # Bot API sticker sets require a valid sticker file and a set name ending in _by_<bot_username>.
    if not BOT_USERNAME:
        return await c.answer('Set BOT_USERNAME in .env first',show_alert=True)
    fmt=job['source_format']
    title=f'RoXeT Emoji {c.from_user.id}'
    try:
        from aiogram.types import InputSticker
        sticker_format='video' if fmt=='WEBM' else 'static'
        inp=InputSticker(sticker=FSInputFile(job['result_path']),format=sticker_format,emoji_list=['✨'])
        pack=get_user_pack(c.from_user.id)
        if pack:
            name=pack['pack_name']
            await bot.add_sticker_to_set(user_id=c.from_user.id,name=name,sticker=inp)
        else:
            name=f'roxet_{c.from_user.id}_by_{BOT_USERNAME}'.lower()
            await bot.create_new_sticker_set(user_id=c.from_user.id,name=name,title=title,stickers=[inp],sticker_type='custom_emoji')
            save_user_pack(c.from_user.id,name,title)
        link=f'https://t.me/addemoji/{name}'
        with db() as con: con.execute("UPDATE jobs SET pack_name=?,status='packed' WHERE id=?",(name,jid))
        await c.message.answer(t(lang_of(c.from_user.id),'added')+'\n'+link)
        await c.message.edit_reply_markup(reply_markup=None); await c.answer('Added')
    except Exception as e:
        await c.answer(str(e)[:180],show_alert=True)
@dp.message()
async def receive_emoji_or_id(m:Message):
    if not m.from_user: return
    emoji_id=None
    for ent in (m.entities or []):
        if ent.type=='custom_emoji' and ent.custom_emoji_id:
            emoji_id=ent.custom_emoji_id; break
    text_value=(m.text or '').strip()
    if not emoji_id and text_value.isdigit(): emoji_id=text_value
    if not emoji_id: return
    lang=lang_of(m.from_user.id)
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r=await client.post(f'https://api.telegram.org/bot{BOT_TOKEN}/getCustomEmojiStickers',json={'custom_emoji_ids':[emoji_id]})
            data=r.json()
        if not data.get('ok') or not data.get('result'):
            return await m.answer('ایموجی پیدا نشد.' if lang=='fa' else 'Emoji not found.')
        sticker=data['result'][0]
        fmt='TGS' if sticker.get('is_animated') else 'WEBM' if sticker.get('is_video') else 'WEBP'
        kb=None
        if WEBAPP_URL:
            kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(lang,'open'),web_app=WebAppInfo(url=f'{WEBAPP_URL}?emoji_id={emoji_id}'))]])
        caption=(f"ایموجی پیدا شد: {sticker.get('emoji','')} · {fmt}\nبرای تغییر اسم یا لوگو وارد مینی‌اپ شو." if lang=='fa'
                 else f"Emoji found: {sticker.get('emoji','')} · {fmt}\nOpen the Mini App to replace its name or logo.")
        await m.answer(caption,reply_markup=kb)
    except Exception:
        await m.answer(t(lang,'failed'))

async def worker():
    while True:
        with db() as c:
            row=c.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY id LIMIT 1").fetchone()
        if row:
            with db() as c: c.execute("UPDATE jobs SET status='processing' WHERE id=? AND status='queued'",(row['id'],))
            await process_job(dict(row))
        else: await asyncio.sleep(2)
async def main():
    init()
    if not BOT_TOKEN: raise RuntimeError('Set BOT_TOKEN in .env')
    asyncio.create_task(worker())
    await dp.start_polling(bot)
