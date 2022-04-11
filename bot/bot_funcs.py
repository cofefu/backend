from datetime import datetime
from telebot import types

from bot import bot
from app.models import *


def gen_markup(order_number: int):
    markup_btns = types.InlineKeyboardMarkup(row_width=2)
    markup_btns.add(
        types.InlineKeyboardButton('Принять', callback_data=f'{1} {order_number}'),
        types.InlineKeyboardButton('Отклонить', callback_data=f'{2} {order_number}')
    )
    return markup_btns


def send_order(order_number: int):
    order = Order.get_or_none(order_number)
    products = OrderedProduct.select().where(OrderedProduct.order == order)
    time = datetime.strptime(order.time, '%Y-%m-%d %H:%M:%S%z')

    message = f'<b>Заказ №{order_number}</b>\n'
    message += f'<i>Содержание:</i>\n'

    for prod in products:
        message += f'  - {prod.product.product.name} {prod.product.size}мл'
        for top in ToppingToProduct.select().where(ToppingToProduct.ordered_product == prod):
            message += f' + {top.topping.name}'
        message += '\n'

    message += f'<i>Приготовить к:</i> {time.strftime("%H:%M")}\n'
    message += f'<i>Имя покупателя:</i> {order.customer.name}\n'
    if order.customer.phone_number is not None:
        message += f'<i>Телефон покупателя:</i> +7{order.customer.phone_number}\n'

    bot.send_message(chat_id=order.coffee_house.chat_id, text=message, parse_mode='HTML',
                     reply_markup=gen_markup(order_number))
