
#!/usr/bin/env python3
# RoXeT Emoji Extractor

import asyncio
import getpass
import logging
import re
import uuid
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


# ---------------- CONFIG ----------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

LOG = logging.getLogger("RoXeT")

SAVE_DIR = Path("emoji_files")
SAVE_DIR.mkdir(exist_ok=True)


# ---------------- KEYBOARD ----------------

def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✨ استخراج با ایموجی",
                callback_data="extract",
                style="primary",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔎 جستجو با ID",
                callback_data="search_id",
                style="success",
            ),
        ],
        [
            InlineKeyboardButton(
                "📘 راهنما",
                callback_data="help",
                style="danger",
            ),
        ],
        [
            InlineKeyboardButton(
                "💎 درباره RoXeT",
                callback_data="about",
                style="primary",
            ),
        ],
    ])


def back_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⬅️ منوی اصلی",
                callback_data="home",
                style="primary",
            )
        ]
    ])


# ---------------- FILE HELPERS ----------------

def safe_filename(name):
    return re.sub(
        r"[^A-Za-z0-9._-]+",
        "_",
        name or "emoji",
    )[:100] or "emoji"


def document_filename(doc):
    for attr in getattr(doc, "attributes", []) or []:
        if isinstance(attr, DocumentAttributeFilename):
            if attr.file_name:
                return safe_filename(attr.file_name)

    mime = getattr(doc, "mime_type", "") or ""

    extensions = {
        "application/x-tgsticker": ".tgs",
        "video/webm": ".webm",
        "image/webp": ".webp",
    }

    ext = extensions.get(mime, ".bin")
    return f"emoji_{doc.id}{ext}"


# ---------------- MAIN ----------------

async def main():

    print("\n================================")
    print("       RoXeT Emoji Extractor")
    print("================================\n")

    token = getpass.getpass("Bot Token: ").strip()
    api_id_text = input("Telegram API ID: ").strip()
    api_hash = getpass.getpass("Telegram API HASH: ").strip()
    owner_text = input("Owner Telegram ID: ").strip()
    phone = input("Phone Number: ").strip()

    if not all([token, api_id_text, api_hash, owner_text, phone]):
        raise SystemExit("Missing credentials.")

    try:
        api_id = int(api_id_text)
        owner_id = int(owner_text)
    except ValueError:
        raise SystemExit("API ID and Owner ID must be numeric.")

    # Telethon user session
    user_client = TelegramClient(
        "roxet_emoji_user",
        api_id,
        api_hash,
    )

    await user_client.start(phone=phone)

    print("\nTelegram account connected successfully!")

    # ---------------- ACCESS ----------------

    def is_owner(update):
        user = update.effective_user
        return bool(user and user.id == owner_id)

    # ---------------- START ----------------

    async def start_cmd(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):

        if not is_owner(update):
            await update.effective_message.reply_text(
                "⛔ این ربات خصوصی است."
            )
            return

        context.user_data.pop("waiting_for_id", None)

        await update.effective_message.reply_text(
            "<b>💎 RoXeT Emoji Extractor</b>\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "✨ استخراج ایموجی پریمیوم تلگرام\n"
            "🔎 جست‌وجو با شناسه ایموجی\n"
            "🎞 دریافت فایل اصلی در صورت دسترسی\n\n"
            "یکی از گزینه‌های زیر را انتخاب کن:",
            parse_mode="HTML",
            reply_markup=main_menu(),
        )

    # ---------------- BUTTONS ----------------

    async def button_handler(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):

        q = update.callback_query

        if not q:
            return

        if q.from_user.id != owner_id:
            await q.answer(
                "⛔ دسترسی غیرمجاز",
                show_alert=True,
            )
            return

        await q.answer()

        if q.data == "extract":
            context.user_data.pop("waiting_for_id", None)

            text = (
                "<b>✨ استخراج ایموجی</b>\n\n"
                "ایموجی Premium را مستقیم در یک پیام ارسال کن.\n\n"
                "ربات شناسه و فایل آن را بررسی می‌کند."
            )

        elif q.data == "search_id":
            context.user_data["waiting_for_id"] = True

            text = (
                "<b>🔎 جست‌وجو با Emoji ID</b>\n\n"
                "شناسه عددی ایموجی را ارسال کن.\n\n"
                "مثال:\n"
                "<code>5368324170671202286</code>"
            )

        elif q.data == "help":
            text = (
                "<b>📘 راهنمای RoXeT</b>\n\n"
                "1️⃣ استخراج با ایموجی:\n"
                "خود ایموجی را ارسال کن.\n\n"
                "2️⃣ جست‌وجو با ID:\n"
                "شناسه عددی را وارد کن.\n\n"
                "3️⃣ فایل اصلی:\n"
                "در صورت دسترسی تلگرام دریافت می‌شود."
            )

        elif q.data == "about":
            text = (
                "<b>💎 RoXeT Emoji Extractor</b>\n\n"
                "ابزار خصوصی دریافت اطلاعات ایموجی تلگرام.\n"
                "ساخته شده با Python و Telethon."
            )

        elif q.data == "home":
            context.user_data.pop("waiting_for_id", None)

            await q.edit_message_text(
                "<b>💎 RoXeT Emoji Extractor</b>\n\n"
                "گزینه موردنظر را انتخاب کن:",
                parse_mode="HTML",
                reply_markup=main_menu(),
            )
            return

        else:
            text = "دستور نامعتبر است."

        await q.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=back_menu(),
        )

    # ---------------- EXTRACT DOCUMENT ----------------

    async def extract_document(
        msg,
        context,
        emoji_id,
    ):

        await msg.reply_text(
            f"🔎 شناسه:\n<code>{emoji_id}</code>\n\n"
            "⏳ در حال جست‌وجوی فایل اصلی...",
            parse_mode="HTML",
        )

        try:
            docs = await user_client(
                GetCustomEmojiDocumentsRequest(
                    document_id=[emoji_id]
                )
            )

            if not docs:
                await msg.reply_text(
                    "❌ سندی برای این شناسه پیدا نشد."
                )
                return

            for doc in docs:

                filename = document_filename(doc)

                # جلوگیری از تداخل نام فایل
                unique_name = (
                    f"{uuid.uuid4().hex[:8]}_{filename}"
                )

                path = SAVE_DIR / unique_name

                downloaded = await user_client.download_media(
                    doc,
                    file=str(path),
                )

                if not downloaded or not path.exists():
                    await msg.reply_text(
                        "❌ دریافت فایل ناموفق بود."
                    )
                    continue

                mime = getattr(doc, "mime_type", "") or ""

                await msg.reply_text(
                    f"🟢 ایموجی پیدا شد!\n\n"
                    f"🆔 Custom Emoji ID:\n"
                    f"<code>{emoji_id}</code>\n\n"
                    f"📁 فایل: {filename}\n"
                    f"📦 نوع: {mime or 'نامشخص'}",
                    parse_mode="HTML",
                )

                # ارسال به صورت استیکر در صورت پشتیبانی
                if path.suffix.lower() in (
                    ".tgs",
                    ".webm",
                    ".webp",
                ):
                    try:
                        with path.open("rb") as sticker:
                            await context.bot.send_sticker(
                                chat_id=msg.chat_id,
                                sticker=sticker,
                            )
                    except Exception:
                        LOG.exception("Sticker sending failed")

                        await msg.reply_text(
                            "⚠️ ارسال به شکل استیکر ممکن نشد؛ "
                            "فایل اصلی ارسال خواهد شد."
                        )

                # ارسال فایل اصلی
                with path.open("rb") as file:
                    await context.bot.send_document(
                        chat_id=msg.chat_id,
                        document=file,
                        filename=filename,
                        caption=(
                            "💎 RoXeT Emoji Extractor\n"
                            f"🆔 ID: {emoji_id}\n"
                            f"📁 {filename}"
                        ),
                    )

                path.unlink(missing_ok=True)

        except Exception as exc:
            LOG.exception("Extraction error")

            await msg.reply_text(
                f"❌ خطا در استخراج:\n"
                f"{type(exc).__name__}"
            )

    # ---------------- MESSAGE HANDLER ----------------

    async def emoji_handler(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):

        msg = update.effective_message

        if not is_owner(update):
            if msg:
                await msg.reply_text(
                    "⛔ فقط صاحب ربات اجازه استفاده دارد."
                )
            return

        if not msg or not msg.text:
            return

        # ID search mode
        if context.user_data.get("waiting_for_id"):

            value = msg.text.strip()

            if not re.fullmatch(r"\d{1,30}", value):
                await msg.reply_text(
                    "❌ شناسه باید فقط شامل عدد باشد."
                )
                return

            context.user_data.pop("waiting_for_id", None)

            await extract_document(
                msg,
                context,
                int(value),
            )
            return

        # Detect custom emoji entities
        ids = [
            int(entity.custom_emoji_id)
            for entity in (msg.entities or [])
            if entity.type == "custom_emoji"
            and entity.custom_emoji_id
        ]

        if not ids:
            # Accept numeric ID without pressing the menu first
            if re.fullmatch(r"\d{1,30}", msg.text.strip()):
                await extract_document(
                    msg,
                    context,
                    int(msg.text.strip()),
                )
                return

            await msg.reply_text(
                "❌ ایموجی سفارشی شناسایی نشد.\n\n"
                "خود ایموجی را ارسال کن یا از منو "
                "گزینه جست‌وجو با ID را انتخاب کن.",
                reply_markup=main_menu(),
            )
            return

        for emoji_id in ids:
            await extract_document(
                msg,
                context,
                emoji_id,
            )

    # ---------------- APPLICATION ----------------

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start_cmd))

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            emoji_handler,
        )
    )

    print("\n================================")
    print(" RoXeT Emoji Bot is running!")
    print("================================\n")

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
