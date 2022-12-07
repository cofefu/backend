from datetime import datetime, timedelta

from fastapi import APIRouter
import telebot
from pydantic import AnyHttpUrl

from app.models import Order, ban_customer, Customer, OrderStatuses
from bot.filters import bind_bot_filters
from db import SessionLocal
from fastapiProject.settings import settings

from bot.keyboards import gen_send_contact_button

import bot.urls_private
import bot.urls_groups

from bot import bot

router = APIRouter(prefix='/bot')
B_TOKEN = settings.bot_token.replace(':', '_')


def set_webhook():
    # webhook_url = f'https://{settings.domain}:{settings.bot_port}' + f'/bot/{B_TOKEN}/'
    webhook_url = AnyHttpUrl.build(
        scheme='https',
        host=settings.domain,
        port=str(settings.bot_port),
        path=f'/{settings.bot_prefix}/bot/{B_TOKEN}/'
    )
    if bot.get_webhook_info().url != webhook_url:
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)


def order_not_picked(order: Order):
    db = SessionLocal()
    customer = order.customer
    if db.query(Order) \
            .filter_by(customer_id=customer.id, status=OrderStatuses.no_taken) \
            .count() >= settings.max_not_picked_orders:
        ban_customer(customer, datetime.utcnow(), forever=True)
    db.close()


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
