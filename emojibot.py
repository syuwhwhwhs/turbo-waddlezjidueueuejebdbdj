
#!/usr/bin/env python3
"""RoXeT Emoji Extractor - Private Telegram Custom Emoji Bot."""

import asyncio
import getpass
import logging
import re
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from telethon import TelegramClient
from telethon.tl.functions.messages import GetCustomEmojiDocumentsRequest
from telethon.tl.types import DocumentAttributeFilename

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

LOG = logging.getLogger("roxet-emoji")

SAVE_DIR = Path("emoji_files")
SAVE_DIR.mkdir(exist_ok=True)


def safe_filename(name):
    return re.sub(
        r"[^A-Za-z0-9._-]+",
        "_",
        name or "emoji"
    )[:100] or "emoji"


def document_filename(doc):
    for attr in getattr(doc, "attributes", []) or []:
        if isinstance(attr, DocumentAttributeFilename):
            if attr.file_name:
                return safe_filename(attr.file_name)

    mime = getattr(doc, "mime_type", "") or ""

    ext = {
        "application/x-tgsticker": ".tgs",
        "video/webm": ".webm",
        "image/webp": ".webp",
    }.get(mime, ".bin")

    return f"emoji_{getattr(doc, 'id', 'file')}{ext}"


def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✨ استخراج ایموجی",
                callback_data="extract",
            ),
        ],
        [
            InlineKeyboardButton(
                "📘 راهنما",
                callback_data="help",
            ),
            InlineKeyboardButton(
                "ℹ️ درباره",
                callback_data="about",
            ),
        ],
    ])


async def main():
    print("================================")
    print("       RoXeT Emoji Extractor")
    print("================================")

    token = getpass.getpass("Bot Token: ").strip()
    api_id_text = input("Telegram API ID: ").strip()
    api_hash = getpass.getpass("Telegram API HASH: ").strip()
    owner_text = input("Owner Telegram ID: ").strip()
    phone = input("Phone number: ").strip()

    if not all([token, api_hash, phone]):
        raise SystemExit("Missing credentials.")

    try:
        api_id = int(api_id_text)
        owner_id = int(owner_text)
    except ValueError:
        raise SystemExit("API ID and Owner ID must be numeric.")

    user_client = TelegramClient(
        "roxet_emoji_user",
        api_id,
        api_hash,
    )

    await user_client.start(phone=phone)

    print("Telegram user session connected.")

    async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != owner_id:
            await update.effective_message.reply_text(
                "⛔ این ربات خصوصی است."
            )
            return

        await update.effective_message.reply_text(
            "<b>✨ RoXeT Emoji Extractor</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🎞 استخراج شناسه و فایل اصلی ایموجی\n\n"
            "ایموجی Premium را مستقیم ارسال کن.",
            parse_mode="HTML",
            reply_markup=main_menu(),
        )

    async def button_handler(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        q = update.callback_query

        if not q:
            return

        if q.from_user.id != owner_id:
            await q.answer(
                "دسترسی فقط برای مالک ربات مجاز است.",
                show_alert=True,
            )
            return

        await q.answer()

        if q.data == "extract":
            text = (
                "<b>✨ استخراج ایموجی</b>\n\n"
                "ایموجی سفارشی تلگرام را مستقیم ارسال کن."
            )

        elif q.data == "help":
            text = (
                "<b>📘 راهنمای استفاده</b>\n\n"
                "۱. ایموجی Premium را ارسال کن.\n"
                "۲. ربات شناسه را شناسایی می‌کند.\n"
                "۳. فایل اصلی در صورت دسترسی ارسال می‌شود."
            )

        elif q.data == "about":
            text = (
                "<b>RoXeT Emoji Extractor</b>\n\n"
                "ربات خصوصی استخراج اطلاعات ایموجی تلگرام."
            )

        else:
            text = (
                "<b>✨ RoXeT Emoji Extractor</b>\n"
                "ایموجی Premium را مستقیم ارسال کن."
            )

        await q.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ منوی اصلی",
                        callback_data="home",
                    )
                ]
            ]),
        )

    async def emoji_handler(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        user = update.effective_user
        msg = update.effective_message

        if not user or user.id != owner_id:
            if msg:
                await msg.reply_text(
                    "⛔ دسترسی فقط برای صاحب ربات مجاز است."
                )
            return

        if not msg or not msg.text:
            return

        ids = [
            int(entity.custom_emoji_id)
            for entity in (msg.entities or [])
            if entity.type == "custom_emoji"
            and entity.custom_emoji_id
        ]

        if not ids:
            await msg.reply_text(
                "❌ ایموجی سفارشی شناسایی نشد.\n"
                "لطفاً خود ایموجی را مستقیم ارسال کن."
            )
            return

        await msg.reply_text(
            f"💎 تعداد ایموجی شناسایی‌شده: {len(ids)}\n"
            f"🆔 ID: <code>{ids[0]}</code>\n"
            "⏳ در حال دریافت فایل اصلی...",
            parse_mode="HTML",
        )

        try:
            docs = await user_client(
                GetCustomEmojiDocumentsRequest(
                    document_id=ids
                )
            )

            if not docs:
                await msg.reply_text(
                    "❌ تلگرام سندی برای این ایموجی برنگرداند."
                )
                return

            for doc in docs:
                filename = document_filename(doc)
                path = SAVE_DIR / filename

                downloaded = await user_client.download_media(
                    doc,
                    file=str(path),
                )

                if not downloaded or not path.exists():
                    await msg.reply_text(
                        "❌ دانلود فایل ناموفق بود."
                    )
                    continue

                with path.open("rb") as file:
                    await context.bot.send_document(
                        chat_id=msg.chat_id,
                        document=file,
                        filename=filename,
                        caption=(
                            "✅ فایل اصلی ایموجی\n"
                            f"🆔 Custom Emoji ID: {ids[0]}\n"
                            f"📁 File: {filename}"
                        ),
                    )

                await msg.reply_text(
                    f"✅ فایل دریافت شد: {filename}"
                )

        except Exception as exc:
            LOG.exception("Emoji extraction failed")
            await msg.reply_text(
                f"❌ خطا در دریافت فایل:\n"
                f"{type(exc).__name__}"
            )

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            emoji_handler,
        )
    )

    print("RoXeT Emoji Bot Started!")

    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(
            drop_pending_updates=True
        )
        await asyncio.Event().wait()

    finally:
        if app.updater.running:
            await app.updater.stop()

        if app.running:
            await app.stop()

        await app.shutdown()
        await user_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
