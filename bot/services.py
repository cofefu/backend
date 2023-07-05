from pytz import timezone

from bot import bot
from db.models import *
from bot.keyboards import gen_order_confirmed_buttons
from db import SessionLocal
from fastapiProject.settings import settings


def gen_order_msg_text(order_id: int) -> str:
    db = SessionLocal()
    order: Order = db.query(Order).get(order_id)
    products: list[ProductInOrder] = order.products_in_order

    message = f'<b>Заказ №{order.order_number}</b>\n'
    message += f'<i>Содержание:</i>\n'

    for prod in products:
        message += f'  - {prod.product_various.product.name}, размер {prod.product_various.size_name}'
        top: Topping2ProductInOrder
        for top in prod.toppings:
            message += f' + {top.topping.name}'
        message += '\n'

    if order.comment:
        message += f'<i>Комментарий:</i> {order.comment}\n'

    order_time = order.time.astimezone(tz=timezone('Asia/Vladivostok'))
    message += f'<i>Приготовить к:</i> {order_time.strftime("%H:%M")}\n'
    message += f'<i>Имя покупателя:</i> {order.customer.name}\n'
    message += f'<i>Телефон покупателя:</i> +7{order.customer_phone_number}\n'

    db.close()
    return message


def send_order(order_id: int):
    db = SessionLocal()
    if (order := db.query(Order).get(order_id)) is not None:
        bot.send_message(chat_id=order.coffee_house_branch.chat_id,
                         text=gen_order_msg_text(order_id),
                         parse_mode='HTML',
                         reply_markup=gen_order_confirmed_buttons(order_id))
    db.close()


def send_login_code_to_telegram(login_code: LoginCode):
    msg = f'Код для входа: {login_code.code}'
    bot.send_message(chat_id=login_code.customer.chat_id, text=msg)


def send_feedback_to_telegram(msg: str):
    msg = '<b>FEED BACK</b>\n' + msg
    bot.send_message(chat_id=settings.feedback_chat, text=msg, parse_mode='HTML')


def send_bugreport_to_telegram(msg: str, customer: Customer = None):
    msg_text = '<b>BUG REPORT</b>\n' + msg
    if customer:
        msg_text += f'\n<b>Номер телефона: +7{customer.phone_number}</b>'
    bot.send_message(chat_id=settings.feedback_chat, text=msg_text, parse_mode='HTML')


def notify_order_change(order: Order):
    text = f'Заказ №{order.order_number} <b>{order.get_status_name()}</b>.\n'
    text += f'Кофейня {order.coffee_house_branch.coffee_house_name} в {order.coffee_house_branch.placement}'

    bot.send_message(chat_id=order.customer.chat_id, text=text, parse_mode='HTML')
