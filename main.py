import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import Message, Update

# Токен из переменных окружения Render
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN is required")

# Aiogram v3: parse_mode задаём через DefaultBotProperties
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Хендлеры
@dp.message(CommandStart())
async def on_start(m: Message):
    await m.answer("Привет! Я жив. Напиши что-нибудь — отвечу тем же 😊")

@dp.message(F.text)
async def echo(m: Message):
    await m.answer(f"Эхо: <b>{m.text}</b>")

# FastAPI приложение + один маршрут вебхука
app = FastAPI()

@app.get("/ping")
async def ping():
    return {"ok": True}

# Вебхук без секретов: путь фиксированный /tg
@app.post("/tg")
async def tg_webhook(request: Request):
    data = await request.json()
    update = Update.model_validate(data)   # aiogram v3
    await dp.feed_update(bot, update)
    return JSONResponse({"ok": True})

