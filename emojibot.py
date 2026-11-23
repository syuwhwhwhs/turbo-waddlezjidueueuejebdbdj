import requests
from pathlib import Path

BOT_TOKEN = "8987582737:AAFIa1hbNPi4yFJ4_c7-JMJTcX_jPrpzOgw"

# Custom Emoji ID
EMOJI_ID = "6010097807745094965"

API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# دریافت اطلاعات فایل
r = requests.post(
    f"{API}/getCustomEmojiStickers",
    json={"custom_emoji_ids": [EMOJI_ID]}
)
r.raise_for_status()

data = r.json()

if not data["ok"] or not data["result"]:
    raise Exception(data)

sticker = data["result"][0]
file_id = sticker["file_id"]

# دریافت مسیر فایل
r = requests.get(
    f"{API}/getFile",
    params={"file_id": file_id}
)
r.raise_for_status()

file_path = r.json()["result"]["file_path"]

# دانلود فایل اصلی
url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

content = requests.get(url)
content.raise_for_status()

output = Path("downloaded_emojis")
output.mkdir(exist_ok=True)

save_path = output / Path(file_path).name
save_path.write_bytes(content.content)

print("Downloaded:", save_path)
print("Format:", save_path.suffix)
print("Size:", len(content.content), "bytes")

