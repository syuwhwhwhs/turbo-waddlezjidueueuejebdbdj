
# RoXeT Emoji Extractor 💎

Private Telegram Custom Emoji Extractor.

## Features

- Persian Telegram interface
- Inline buttons
- Custom Emoji ID detection
- MTProto integration using Telethon
- Original document download when accessible
- TGS, WEBM and WEBP format support
- Private owner-only access

## Requirements

- Ubuntu 22.04 / 24.04
- Python 3.10+
- Telegram Bot Token
- Telegram API ID
- Telegram API HASH
- Owner Telegram ID
- Telegram phone number

## Installation

```bash
sudo apt update
sudo apt install -y python3-venv

python3 -m venv .venv

.venv/bin/pip install --upgrade pip

.venv/bin/pip install -r requirements.txt
```

## Run

```bash
.venv/bin/python emojibot.py
```

Enter your credentials when prompted.

## Usage

1. Open your Telegram bot.
2. Send /start.
3. Send a custom emoji directly.
4. Receive its ID and original document when available.

## Security

Never upload Telegram session files, bot tokens,
API HASH or private credentials to GitHub.

Keep your Telegram session private.
