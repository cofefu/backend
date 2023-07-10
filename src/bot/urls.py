from fastapi import APIRouter
import telebot
from pydantic import AnyHttpUrl

from src.bot.filters import bind_bot_filters
from src.config.settings import settings

from src.bot.keyboards import gen_send_contact_button

import src.bot.urls_private
import src.bot.urls_groups

from src.bot import bot

router = APIRouter(prefix=settings.bot_prefix)
B_TOKEN = settings.bot_token.replace(':', '_')


def set_webhook():
    # webhook_url = f'https://{settings.domain}:{settings.bot_port}' + f'/bot/{B_TOKEN}/'
    webhook_url = AnyHttpUrl.build(
        scheme='https',
        host=settings.bot_domain,
        port=str(settings.bot_port),
        path=f'{settings.bot_prefix}/{B_TOKEN}/'
    )
    if bot.get_webhook_info().url != webhook_url:
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)


@router.post(f'/{B_TOKEN}/', include_in_schema=False)
def process_webhook(update: dict):
    if update:
        update = telebot.types.Update.de_json(update)
        bot.process_new_updates([update])
    else:
        return


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = gen_send_contact_button()
    if message.chat.type == 'group':
        markup = None
    bot.send_message(message.chat.id, f'Привет! Я бот cofefu.', reply_markup=markup)


@bot.message_handler(commands=['chat_id'])
def send_chat_id(message):
    bot.reply_to(message, message.chat.id)


@router.on_event('startup')
async def on_startup():
    set_webhook()
    bind_bot_filters()
