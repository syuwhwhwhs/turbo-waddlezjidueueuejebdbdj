
import os
import logging
from getpass import getpass
from pathlib import Path

import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

# دریافت توکن هنگام اجرای برنامه
BOT_TOKEN = getpass("توکن ربات را وارد کنید: ").strip()

API = f"https://api.telegram.org/bot{BOT_TOKEN}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ورود به ربات\n"
        "لطفاً آیدی ایموجی پریموم را بدهید تا فایل را بدم"
    )


async def download_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emoji_id = update.message.text.strip()

    if not emoji_id.isdigit():
        await update.message.reply_text(
            "❌ لطفاً فقط آیدی عددی ایموجی پریمیوم را ارسال کنید."
        )
        return

    msg = await update.message.reply_text("⏳ در حال دریافت ایموجی...")

    try:
        # دریافت Custom Emoji
        response = requests.post(
            f"{API}/getCustomEmojiStickers",
            json={"custom_emoji_ids": [emoji_id]},
            timeout=30,
        )
        data = response.json()

        if not data.get("ok") or not data.get("result"):
            await msg.edit_text("❌ ایموجی پیدا نشد یا API دریافت آن را پشتیبانی نمی‌کند.")
            return

        sticker = data["result"][0]
        file_id = sticker["file_id"]

        # دریافت مسیر فایل
        response = requests.get(
            f"{API}/getFile",
            params={"file_id": file_id},
            timeout=30,
        )
        file_data = response.json()

        if not file_data.get("ok"):
            await msg.edit_text("❌ دریافت مسیر فایل ناموفق بود.")
            return

        file_path = file_data["result"]["file_path"]
        file_name = Path(file_path).name

        # دانلود فایل
        download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        response = requests.get(download_url, timeout=60)
        response.raise_for_status()

        # ذخیره موقت روی سرور
        folder = Path("downloaded_emojis")
        folder.mkdir(exist_ok=True)

        save_path = folder / file_name
        save_path.write_bytes(response.content)

        # ارسال فایل به کاربر
        with open(save_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=file_name,
                caption=f"✅ فایل ایموجی دریافت شد\nID: {emoji_id}",
            )

        await msg.delete()

    except Exception as e:
        logging.exception("Emoji download error")
        await msg.edit_text(f"❌ خطا در دریافت ایموجی:\n{e}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "برای دریافت فایل ایموجی پریمیوم:\n"
        "آیدی عددی ایموجی را ارسال کنید."
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_emoji))

    print("Emoji Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
