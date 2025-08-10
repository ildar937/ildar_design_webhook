
import os
import logging
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Update, Message, InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ildar_webhook")

# --- ENV (все берём из Render Environment) ---
BOT_TOKEN = os.getenv("BOT_TOKEN")  # обязательно
PDF_PATH = os.getenv("PDFPATH")     # опционально
PUBLIC_CHANNEL = os.getenv("PUBLICCHANNEL")  # опционально
WEBHOOK_SECRET = os.getenv("WEBHOOKSECRET") or os.getenv("WEBHOOK_SECRET") or "ai123secret"

if not BOT_TOKEN:
    # Остановим сервис сразу, чтобы не ловить «Unauthorized»
    raise RuntimeError("BOT_TOKEN не найден в Environment Variables!")

# --- AIogram v3 ---
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

# Клавиатура
def kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оставить заявку", url="https://t.me/ildarDESIGNBOT")],
            [InlineKeyboardButton(text="Прайс (PDF)", url=PDF_PATH or "https://example.com")],
            [InlineKeyboardButton(text="Открыть канал", url=PUBLIC_CHANNEL or "https://t.me/example")]
        ]
    )

# Тексты
def src_text(s: str) -> str:
    return {
        "site":    "Вы пришли <b>с сайта</b>. Опишите задачу:",
        "pdf":     "Вы пришли <b>из PDF</b>. Напишите, что нужно:",
        "channel": "Вы пришли <b>из канала</b>. Чем помочь?",
    }.get(s, "Готов помочь с AI-дизайном!")

# Хендлеры
@dp.message(CommandStart())
async def on_start(m: Message):
    await m.answer(src_text("site"), reply_markup=kb())

@dp.message(F.text.lower() == "site")
async def on_site(m: Message):
    await m.answer("Принял «site». Продолжаем!", reply_markup=kb())

# --- FastAPI ---
app = FastAPI()

@app.get("/ping")
async def ping():
    return {"ok": True}

@app.post("/tg/{secret}")
async def tg_webhook(secret: str, request: Request):
    # 1) проверяем секрет из URL
    if secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="bad secret")

    # 2) (необязательно) сверим заголовок секрета
    header_secret = request.headers.get("x-telegram-bot-api-secret-token")
    if header_secret and header_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="bad secret header")

    # 3) прогоняем апдейт в aiogram
    data = await request.json()
    update = Update.model_validate(data)  # aiogram v3
    await dp.feed_update(bot, update)
    return {"ok": True}

# Локальный режим (если запускать не на Render)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
