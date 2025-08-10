import os
import logging

from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import Update, Message, InlineKeyboardMarkup, InlineKeyboardButton

# ---------- ЛОГИ ----------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ildar_webhook")

# ---------- ENV ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")
PDF_PATH = os.getenv("PDFPATH")
PUBLIC_CHANNEL = os.getenv("PUBLICCHANNEL")
WEBHOOK_SECRET = os.getenv("WEBHOOKSECRET") or os.getenv("WEBHOOK_SECRET") or "ai123secret"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN отсутствует в Environment Variables Render")

# ---------- AIOGRAM (v3.7+) ----------
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")  # вместо parse_mode в конструкторе
)
dp = Dispatcher()

def kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оставить заявку", url="https://t.me/ildarDESIGNBOT")],
            [InlineKeyboardButton(text="Прайс (PDF)", url=PDF_PATH or "https://example.com")],
            [InlineKeyboardButton(text="Открыть канал", url=PUBLIC_CHANNEL or "https://t.me/example")],
        ]
    )

def src_text(src: str) -> str:
    return {
        "site":    "Вы пришли <b>с сайта</b>. Опишите задачу:",
        "pdf":     "Вы пришли <b>из PDF</b>. Напишите, что нужно:",
        "channel": "Вы пришли <b>из канала</b>. Чем помочь?",
    }.get(src, "Готов помочь с AI‑дизайном!")

@dp.message(CommandStart())
async def on_start(m: Message):
    await m.answer(src_text("site"), reply_markup=kb())

@dp.message(F.text.lower() == "site")
async def on_site(m: Message):
    await m.answer("Принял «site». Что делаем дальше? 🙂", reply_markup=kb())

# ---------- FASTAPI ----------
app = FastAPI()

@app.get("/ping")
async def ping():
    return {"ok": True}

@app.post("/tg/{secret}")
async def tg_webhook(secret: str, request: Request):
    if secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="bad secret")

    # сверка заголовка секрета (если Telegram его прислал)
    header_secret = request.headers.get("x-telegram-bot-api-secret-token")
    if header_secret and header_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="bad secret header")

    data = await request.json()
    update = Update.model_validate(data)  # aiogram v3
    await dp.feed_update(bot, update)
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
