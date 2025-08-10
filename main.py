import os
import logging

from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Update, Message
from aiogram.filters import CommandStart

# ---------- ЛОГИ ----------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("tg_webhook")

# ---------- ENV ----------
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")  # напр.: https://ildar-design-webhook.onrender.com
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "ai123secret").strip()

if not BOT_TOKEN:
    raise RuntimeError("ENV BOT_TOKEN не задан")
if not BASE_URL.startswith("https://"):
    raise RuntimeError("ENV BASE_URL должен быть полным HTTPS-URL вашего сервиса, например: "
                       "https://ildar-design-webhook.onrender.com")

WEBHOOK_PATH = f"/tg/{WEBHOOK_SECRET}"           # путь вебхука
WEBHOOK_URL = f"{BASE_URL}{WEBHOOK_PATH}"        # полный URL

# ---------- TG ----------
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(m: Message):
    await m.answer("Бот жив! ✅\nПопробуй прислать любое сообщение — я просто повторю его.")

@dp.message(F.text)
async def echo(m: Message):
    await m.answer(f"Эхо: {m.text}")

# ---------- APP ----------
app = FastAPI(title="tg-webhook-min")

@app.get("/")
async def root():
    return {"ok": True, "msg": "up"}

@app.get("/debug/webhook")
async def debug_webhook(key: str):
    """Посмотреть, что думает Telegram о вебхуке. Защищено простым ключом ?key=WEBHOOK_SECRET."""
    if key != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="bad key")
    info = await bot.get_webhook_info()
    return info.model_dump()

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    # Проверяем секретный заголовок от Telegram
    header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if header != WEBHOOK_SECRET:
        log.warning("Webhook called with wrong secret header")
        raise HTTPException(status_code=401, detail="unauthorized")

    data = await request.json()
    try:
        update = Update.model_validate(data)
    except Exception as e:
        log.exception("Bad update: %s", e)
        raise HTTPException(status_code=400, detail="bad update")

    try:
        await dp.feed_update(bot, update)
    except Exception:
        log.exception("Error while handling update")
        # Не падаем с 500, чтобы Telegram не засыпал ретрайами
    return {"ok": True}

# ---------- AUTO WEBHOOK ----------
@app.on_event("startup")
async def on_startup():
    try:
        # Ставим вебхук на наш URL (и секрет, чтобы чужие не стучались),
        # а также чистим подвисшие апдейты.
        await bot.set_webhook(
            url=WEBHOOK_URL,
            secret_token=WEBHOOK_SECRET,
            drop_pending_updates=True,
        )
        log.info("Webhook set to %s", WEBHOOK_URL)
    except Exception:
        log.exception("Failed to set webhook")

@app.on_event("shutdown")
async def on_shutdown():
    try:
        await bot.delete_webhook(drop_pending_updates=False)
        await bot.session.close()
        log.info("Webhook deleted and session closed")
    except Exception:
        log.exception("Failed to delete webhook")


