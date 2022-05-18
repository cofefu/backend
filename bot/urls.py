from datetime import datetime, timedelta

from fastapi import APIRouter
import telebot

from app.models import Order, ban_customer, Customer
from bot.filters import bind_bot_filters
from fastapiProject.settings import DOMAIN, BOT_TOKEN, BOT_PORT, DEBUG

from bot.bot_funcs import send_feedback_to_telegram, send_bugreport_to_telegram
from bot.keyboards import gen_send_contact_button

import bot.urls_private
import bot.urls_groups

from bot import bot

router = APIRouter(prefix='/bot')


def set_webhook():
    webhook_url = f"https://{DOMAIN}:{BOT_PORT}" + f'/bot/{BOT_TOKEN}/'
    if not DEBUG and \
            bot.get_webhook_info().url != webhook_url:
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)


def order_not_picked(order: Order):
    customer = order.customer
    if len(customer.customer_orders.where(Order.status == 4)) >= 3:
        ban_customer(customer, datetime.utcnow(), forever=True)


@router.post(f'/{BOT_TOKEN}/', include_in_schema=False)
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
    bot.send_message(message.chat.id, f"Привет! Я бот cofefu.", reply_markup=markup)


@bot.message_handler(commands=['chat_id'])
def send_chat_id(message):
    bot.reply_to(message, message.chat.id)


@router.on_event('startup')
async def on_startup():
    set_webhook()
    bind_bot_filters()
