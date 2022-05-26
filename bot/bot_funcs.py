from datetime import datetime

from fastapiProject.settings import FEEDBACK_CHAT
from bot import bot
from app.models import *
from bot.keyboards import gen_order_confirmed_buttons


def gen_order_msg_text(order_number: int) -> str:
    order = Order.get_or_none(order_number)
    products = OrderedProduct.select().where(OrderedProduct.order == order)

    message = f'<b>Заказ №{order_number}</b>\n'
    message += f'<i>Содержание:</i>\n'

    for prod in products:
        message += f'  - {prod.product.product.name}, размер {prod.product.get_size_name()}'
        for top in ToppingToProduct.select().where(ToppingToProduct.ordered_product == prod):
            message += f' + {top.topping.name}'
        message += '\n'

    if order.comment:
        message += f'<i>Комментарий:</i> {order.comment}\n'

    message += f'<i>Приготовить к:</i> {order.time.strftime("%H:%M")}\n'
    message += f'<i>Имя покупателя:</i> {order.customer.name}\n'
    message += f'<i>Телефон покупателя:</i> +7{order.customer.phone_number}\n'

    return message


def send_order(order_number: int):
    if (order := Order.get_or_none(order_number)) is not None:
        bot.send_message(chat_id=order.coffee_house.chat_id,
                         text=gen_order_msg_text(order_number),
                         parse_mode='HTML',
                         reply_markup=gen_order_confirmed_buttons(order_number))


def send_login_code(login_code: LoginCode):
    msg = f'Код для входа: {login_code.code}'
    bot.send_message(chat_id=login_code.customer.chat_id, text=msg)


def send_feedback_to_telegram(msg: str):
    msg = '<b>FEED BACK</b>\n' + msg
    bot.send_message(chat_id=FEEDBACK_CHAT, text=msg, parse_mode='HTML')


def send_bugreport_to_telegram(msg: str, customer: Customer = None):
    msg_text = '<b>BUG REPORT</b>\n' + msg
    if customer:
        msg_text += f'\n<b>Номер телефона: +7{customer.phone_number}</b>'
    bot.send_message(chat_id=FEEDBACK_CHAT, text=msg_text, parse_mode='HTML')


def notify_order_change(order: Order):
    text = f'Заказ №{order.id} <b>{order.get_status_name()}</b>.\n'
    text += f'Кофейня {order.coffee_house.name} в {order.coffee_house.placement}'

    bot.send_message(chat_id=order.customer.chat_id, text=text, parse_mode='HTML')
