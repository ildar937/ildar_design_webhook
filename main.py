
import logging
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Update, Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
import config

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ildar_webhook")

bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()
app = FastAPI()

def kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оставить заявку", callback_data="lead")],
        [InlineKeyboardButton(text="Прайс (PDF)", callback_data="price")],
        [InlineKeyboardButton(text="Открыть канал", url=f"https://t.me/{config.PUBLIC_CHANNEL_USERNAME}")],
    ])

def src_text(s):
    return {
        "site":"Вы пришли <b>с сайта</b>. Опишите задачу и срок — отвечу быстро.",
        "pdf":"Вы пришли <b>из PDF</b>. Пришлите 1–2 фото товара и дедлайн.",
        "channel":"Вы пришли <b>из канала</b>. Подскажу по формату и срокам."
    }.get(s, "Готов помочь с AI-дизайном карточек, обложек и аватаров.")

@dp.message(CommandStart())
async def start(m: Message):
    payload = m.text.split(' ',1)[1].strip() if m.text and ' ' in m.text else ''
    src = payload or 'direct'
    await m.answer(f"Привет, {m.from_user.full_name}!\n{src_text(src)}", reply_markup=kb())
    if config.MANAGER_CHAT_ID:
        u = m.from_user
        note = f"🆕 Контакт · src:<b>{src}</b>\n@{u.username or '—'} · {u.full_name} · <code>{u.id}</code>"
        try:
            await bot.send_message(config.MANAGER_CHAT_ID, note)
        except Exception as e:
            log.warning("notify fail: %s", e)

@dp.message(Command("id"))
async def my_id(m: Message):
    await m.answer(f"Ваш chat_id: <code>{m.from_user.id}</code>")

@dp.message(Command("price"))
async def price_cmd(m: Message):
    try:
        await m.answer_document(FSInputFile(config.PDF_PATH), caption="Прайс и кейсы (PDF)")
    except Exception as e:
        await m.answer("Прайс недоступен. Проверьте PDF_PATH на сервере.")
        log.error("price error: %s", e)

@dp.callback_query(F.data == "price")
async def cb_price(c):
    await c.answer()
    try:
        await c.message.answer_document(FSInputFile(config.PDF_PATH), caption="Прайс и кейсы (PDF)")
    except Exception as e:
        await c.message.answer("Прайс недоступен.")
        log.error("price error: %s", e)

@dp.callback_query(F.data == "lead")
async def cb_lead(c):
    await c.answer()
    await c.message.answer("Опишите задачу, желаемый стиль и срок. Можно прикрепить 1–2 фото.")

@dp.message(F.photo | F.text)
async def relay(m: Message):
    if not config.MANAGER_CHAT_ID:
        return
    u = m.from_user
    try:
        await bot.send_message(config.MANAGER_CHAT_ID, f"✉️ @{u.username or '—'} · {u.full_name} · <code>{u.id}</code>")
        await m.forward(MANAGER_CHAT_ID := config.MANAGER_CHAT_ID)  # reuse
    except Exception as e:
        log.warning("forward fail: %s", e)

@app.get("/ping")
async def ping():
    return {"ok": True}

@app.on_event("startup")
async def on_startup():
    if not config.BOT_TOKEN:
        log.error("BOT_TOKEN empty")
        return
    if config.BASE_URL:
        try:
            await bot.set_webhook(f"{config.BASE_URL}/tg/{config.WEBHOOK_SECRET}",
                                  secret_token=config.WEBHOOK_SECRET)
            log.info("webhook set")
        except Exception as e:
            log.error("set webhook failed: %s", e)
    else:
        log.info("BASE_URL empty — set after first deploy")

@app.post("/tg/{secret}")
async def tg(secret: str, request: Request):
    if secret != config.WEBHOOK_SECRET:
        raise HTTPException(403, "forbidden")
    update = Update.model_validate(await request.json())
    await dp.feed_update(bot, update)
    return {"ok": True}
