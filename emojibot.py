
import logging
from getpass import getpass
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telethon import TelegramClient
from telethon.tl.functions.messages import GetCustomEmojiDocumentsRequest

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

# اطلاعات ورود در ترمینال سرور، نه در GitHub
BOT_TOKEN = getpass("Bot Token: ").strip()
API_ID = int(input("Telegram API ID: ").strip())
API_HASH = getpass("Telegram API HASH: ").strip()
PHONE = input("Telegram phone (+country code): ").strip()

SESSION_NAME = "emoji_user_session"
DOWNLOAD_DIR = Path("downloaded_emojis")
DOWNLOAD_DIR.mkdir(exist_ok=True)

user_client = TelegramClient(SESSION_NAME, API_ID, API_HASH)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ Emoji Premium Downloader\n\n"
        "ورود به ربات\n"
        "لطفاً آیدی ایموجی پریموم را بدهید تا فایل را بدم\n\n"
        "مثال:\n"
        "6034955549445984368"
    )


async def get_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text("❌ لطفاً فقط آیدی عددی ایموجی را بفرست.")
        return

    status = await update.message.reply_text("🔎 در حال پیدا کردن ایموجی...")

    try:
        result = await user_client(
            GetCustomEmojiDocumentsRequest(document_id=[int(text)])
        )

        if not result:
            await status.edit_text("❌ ایموجی پیدا نشد.")
            return

        document = result[0]

        # فایل اصلی ایموجی دانلود می‌شود
        saved = await user_client.download_media(
            document,
            file=str(DOWNLOAD_DIR) + "/"
        )

        if not saved:
            await status.edit_text("❌ دانلود فایل ناموفق بود.")
            return

        file_path = Path(saved)
        await status.edit_text("📤 در حال ارسال فایل...")

        with open(file_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=file_path.name,
                caption=f"✨ فایل ایموجی دریافت شد\n🆔 {text}"
            )

        await status.delete()

    except Exception as e:
        logging.exception("Emoji extraction failed")
        await status.edit_text(f"❌ خطا:\n{str(e)[:3000]}")


async def main():
    print("🔐 Connecting Telegram user account...")
    await user_client.start(phone=PHONE)
    print("✅ Telegram user connected.")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_emoji))

    print("🚀 Emoji Bot is running!")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    try:
        import asyncio
        await asyncio.Event().wait()
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        await user_client.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
