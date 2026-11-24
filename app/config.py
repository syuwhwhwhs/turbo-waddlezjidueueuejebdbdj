import os
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN=os.getenv("BOT_TOKEN","")
BOT_USERNAME=os.getenv("BOT_USERNAME","").lstrip("@")
WEBAPP_URL=os.getenv("WEBAPP_URL","")
ADMIN_IDS={int(x) for x in os.getenv("ADMIN_IDS","").split(",") if x.strip().isdigit()}
DATABASE_PATH=os.getenv("DATABASE_PATH","data/studio.db")
WORK_DIR=os.getenv("WORK_DIR","data/work")
HOST=os.getenv("HOST","0.0.0.0")
PORT=int(os.getenv("PORT","8000"))
