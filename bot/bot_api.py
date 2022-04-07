from fastapi import APIRouter
import telebot

from app.models import Order
from backend.settings import DOMAIN, SERVER_PORT, API_TOKEN
from bot import bot
from telebot import types
from bot.email_sender import send_email

router = APIRouter()


def gen_send_contact_markup():
    btn = types.InlineKeyboardMarkup()
    btn.add(
        types.InlineKeyboardButton('Подтвердить номер телефона', request_contact=True),
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
    bot.send_message(message.chat.id,
                     f"Hello, i'm coffefu webhook bot.",
                     reply_markup=gen_send_contact_markup())


@bot.message_handler(commands=['chat_id'])
def send_chat_id(message):
    bot.reply_to(message, message.chat.id)


@bot.callback_query_handler(func=lambda call: 'phone' in call.data.split())
def confirm_phone_number(call: types.CallbackQuery):
    bot.send_message(chat_id=call.message.chat.id, text=f"Your phone number is {call.contact.phone_number}")


@bot.callback_query_handler(func=lambda call: 'order' in call.data.split())
def callback_processing(call: types.CallbackQuery):
    _, cb_status, order_number = call.data.split()
    cb_status = int(cb_status)
    order_number = int(order_number)

    order = Order.get_or_none(id=int(order_number))
    order.status = cb_status
    order.save()

    ans = 'Заказ принят' if cb_status == 1 else 'Заказ отклонен'
    bot.answer_callback_query(call.id, ans, show_alert=True)  # todo что за show_alert
    ans = f"\n<b>{ans}</b>"
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=call.message.text + ans, parse_mode='HTML', reply_markup=None)

    # if order.customer.email:
    #     customer_email = order.customer.email
    #     send_email(customer_email, int(order_number), cb_status == 1)  # redo
