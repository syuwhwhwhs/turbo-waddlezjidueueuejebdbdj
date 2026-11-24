#!/usr/bin/env bash
set -euo pipefail
sudo apt update
sudo apt install -y python3-venv python3-pip ffmpeg fonts-noto-core
python3 -m venv .venv
.venv/bin/pip install --upgrade pip wheel
.venv/bin/pip install -r requirements.txt
if [ ! -f .env ]; then cp .env.example .env; fi
mkdir -p data/work data/work/uploads
echo
echo 'نصب وابستگی‌ها انجام شد. اکنون .env را ویرایش کن:'
echo 'nano .env'
echo 'سپس وب‌سرور و ربات را در دو ترمینال جدا اجرا کن.'
