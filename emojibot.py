
import requests
from io import BytesIO
from pathlib import Path
from getpass import getpass

# دریافت توکن هنگام اجرا
BOT_TOKEN = getpass("توکن ربات را وارد کن: ").strip()

API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def get_emoji_file(emoji_id):
    # دریافت اطلاعات ایموجی
    r = requests.post(
        f"{API}/getCustomEmojiStickers",
        json={"custom_emoji_ids": [emoji_id]},
        timeout=30
    )
    r.raise_for_status()
    data = r.json()

    if not data.get("ok") or not data.get("result"):
        raise Exception("ایموجی پیدا نشد یا دسترسی API وجود ندارد")

    sticker = data["result"][0]
    file_id = sticker["file_id"]

    # دریافت مسیر فایل
    r = requests.get(
        f"{API}/getFile",
        params={"file_id": file_id},
        timeout=30
    )
    r.raise_for_status()
    file_data = r.json()

    if not file_data.get("ok"):
        raise Exception("دریافت مسیر فایل ناموفق بود")

    file_path = file_data["result"]["file_path"]

    # دانلود فایل
    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    r = requests.get(url, timeout=60)
    r.raise_for_status()

    return Path(file_path).name, r.content


def main():
    print("Emoji Downloader")
    print("برای خروج exit بنویس")

    while True:
        emoji_id = input("\nشناسه ایموجی: ").strip()

        if emoji_id.lower() == "exit":
            break

        if not emoji_id.isdigit():
            print("❌ شناسه باید عددی باشد")
            continue

        try:
            filename, content = get_emoji_file(emoji_id)

            # ذخیره فایل روی سرور
            output = Path("downloaded_emojis")
            output.mkdir(exist_ok=True)
            save_path = output / filename
            save_path.write_bytes(content)

            print("✅ دانلود موفق")
            print("فایل:", save_path)
            print("فرمت:", save_path.suffix)
            print("حجم:", len(content), "bytes")

        except Exception as e:
            print("❌ خطا:", e)


if __name__ == "__main__":
    main()
