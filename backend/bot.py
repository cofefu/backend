import os

from aiogram import Dispatcher, Bot, types
from .server import app

TOKEN = "1945118170:AAH4ZVOXOgEC8F3wDCB-rZ81817fynT7INk"
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands="start")
async def start(message: types.Message):
    await message.answer(f"Salom, {message.from_user.full_name}")


WEBHOOK_PATH = f"/bot/{os.getenv('BOT_TOKEN')}"
WEBHOOK_URL = f"{os.getenv('BOT_URL')}" + WEBHOOK_PATH


@app.on_event("startup")
async def on_startup():
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        await bot.set_webhook(url=WEBHOOK_URL)


@app.post(WEBHOOK_PATH)
async def bot_webhook(update: dict):
    telegram_update = types.Update(**update)
    Dispatcher.set_current(dp)
    Bot.set_current(bot)
    await dp.process_update(telegram_update)


@app.on_event("shutdown")
async def on_shutdown():
    await bot.session.close()


__all__ = ['on_startup', 'bot_webhook', 'on_shutdown']
