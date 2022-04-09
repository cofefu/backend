from fastapi import APIRouter
import telebot

from app.models import Order, Customer
from backend.settings import DOMAIN, SERVER_PORT, API_TOKEN
from bot import bot
from telebot import types
from bot.email_sender import send_email

router = APIRouter()


def gen_send_contact_markup():
    btn = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn.add(
        types.KeyboardButton('Подтвердить номер телефона', request_contact=True)
    )
    return btn


def set_webhook():
    webhook_url = f"https://{DOMAIN}:{SERVER_PORT}" + f'/bot/{API_TOKEN}/'
    if bot.get_webhook_info().url != webhook_url:
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)


@router.post(f'/{API_TOKEN}/', include_in_schema=False)
def process_webhook(update: dict):
    if update:
        update = telebot.types.Update.de_json(update)
        bot.process_new_updates([update])
    else:
        return


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = gen_send_contact_markup()
    if message.chat.type == 'group':
        markup = None
    bot.send_message(message.chat.id,
                     f"Hello, i'm cofefu webhook bot.",
                     reply_markup=markup)


@bot.message_handler(commands=['chat_id'])
def send_chat_id(message):
    bot.reply_to(message, message.chat.id)


@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    phone_number = message.contact.phone_number
    if message.contact.user_id != message.from_user.id:
        bot.send_message(chat_id=message.chat.id, text='Это НЕ ваш номер телефона.')
        return

    if customer := Customer.get_or_none(phone_number=phone_number):
        customer.confirmed = True
        customer.chat_id = message.chat.id
        customer.save()

        bot.send_message(chat_id=message.chat.id,
                         text='Номер телефона подтвержден.',
                         reply_markup=types.ReplyKeyboardRemove(selective=False))
    else:
        bot.send_message(chat_id=message.chat.id,
                         text='Пользователь с таким номером телефона не найден.')


@bot.callback_query_handler(func=lambda call: True)
def callback_processing(call: types.CallbackQuery):
    cb_status, order_number = map(int, call.data.split())
    order = Order.get_or_none(id=int(order_number))
    order.status = cb_status
    order.save()

    ans = 'Заказ принят' if cb_status == 1 else 'Заказ отклонен'
    bot.answer_callback_query(call.id, ans)
    ans = f"\n<b>{ans}</b>"
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=call.message.text + ans, parse_mode='HTML', reply_markup=None)
