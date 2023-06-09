from bot import bot
from app.models import *
from bot.keyboards import gen_order_confirmed_buttons
from db import SessionLocal
from fastapiProject.settings import settings


def gen_order_msg_text(order_number: int) -> str:
    db = SessionLocal()
    order: Order = db.get(Order, order_number)
    products: list[ProductInOrder, ...] = db.query(ProductInOrder).filter_by(order_id=order_number).all()

    message = f'<b>Заказ №{order_number}</b>\n'
    message += f'<i>Содержание:</i>\n'

    for prod in products:
        message += f'  - {prod.product_various.product_various.name}, размер {prod.product_various.size.value}'
        for top in db.query(Topping2ProductInOrder).filter_by(ordered_product_id=prod.id):
            message += f' + {top.topping.name}'
        message += '\n'

    if order.comment:
        message += f'<i>Комментарий:</i> {order.comment}\n'

    message += f'<i>Приготовить к:</i> {order.time.strftime("%H:%M")}\n'
    message += f'<i>Имя покупателя:</i> {order.customer.name}\n'
    message += f'<i>Телефон покупателя:</i> +7{order.customer.phone_number}\n'

    db.close()
    return message


def send_order(order_number: int):
    db = SessionLocal()
    if (order := db.get(Order, order_number)) is not None:
        bot.send_message(chat_id=order.coffee_house.chat_id,
                         text=gen_order_msg_text(order_number),
                         parse_mode='HTML',
                         reply_markup=gen_order_confirmed_buttons(order_number))
    db.close()


def send_login_code(login_code: LoginCode):
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
    text = f'Заказ №{order.id} <b>{order.get_status_name()}</b>.\n'
    text += f'Кофейня {order.coffee_house.name} в {order.coffee_house.placement}'

    bot.send_message(chat_id=order.customer.chat_id, text=text, parse_mode='HTML')
