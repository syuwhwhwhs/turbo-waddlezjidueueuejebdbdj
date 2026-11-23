#!/bin/bash
set -e
[ "$EUID" -ne 0 ] && echo "Run as root: sudo su" && exit 1

REPO="https://github.com/syuwhwhwhs/turbo-waddlezjidueueuejebdbdj.git"
DIR="/opt/roxet-emoji"

apt update
apt install -y git python3-venv screen

if [ -d "$DIR/.git" ]; then
  git -C "$DIR" pull
else
  git clone "$REPO" "$DIR"
fi

cd "$DIR"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

cat > /etc/systemd/system/roxet-emoji.service <<EOF
[Unit]
Description=RoXeT Emoji Extractor
After=network.target

[Service]
WorkingDirectory=$DIR
ExecStart=$DIR/.venv/bin/python emojibot.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload

echo "Installed. First login run:"
echo "  cd $DIR && .venv/bin/python emojibot.py"
echo "After login works, press Ctrl+C then:"
echo "  systemctl enable --now roxet-emoji"
