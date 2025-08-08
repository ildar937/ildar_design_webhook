
import os
BOT_TOKEN = os.getenv("BOT_TOKEN","").strip()
BASE_URL  = os.getenv("BASE_URL","").rstrip("/")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET","ai123secret")
PUBLIC_CHANNEL_USERNAME = os.getenv("PUBLIC_CHANNEL_USERNAME","ai_do_after")
MANAGER_CHAT_ID = int(os.getenv("MANAGER_CHAT_ID","0") or 0)
PDF_PATH = os.getenv("PDF_PATH","assets/price.pdf")
