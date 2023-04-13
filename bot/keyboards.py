from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from app.models import Order
from bot.filters import order_callback_confirmed, order_callback_done, order_callback_ready, order_cancel_reason, \
    CancelReasons, special_problem
from db import SessionLocal


def gen_send_contact_button() -> ReplyKeyboardMarkup:
    btn = ReplyKeyboardMarkup(resize_keyboard=True)
    btn.add(
        KeyboardButton('Подтвердить номер телефона', request_contact=True)
    )
    return btn


def gen_order_done_buttons(order_number: int) -> InlineKeyboardMarkup:
    markup_btns = InlineKeyboardMarkup(row_width=2)
    markup_btns.add(
        InlineKeyboardButton('Выполнен',
                             callback_data=order_callback_done.new(order_number, status=int(True))),
        InlineKeyboardButton('Не выполнен',
                             callback_data=order_callback_done.new(order_number, status=int(False)))
    )
    return markup_btns


def gen_order_confirmed_buttons(order_number: int) -> InlineKeyboardMarkup:
    markup_btns = InlineKeyboardMarkup(row_width=2)
    markup_btns.add(
        InlineKeyboardButton('Принять',
                             callback_data=order_callback_confirmed.new(order_number, status=int(True))),
        InlineKeyboardButton('Отклонить',
                             callback_data=order_callback_confirmed.new(order_number, status=int(False)))
    )
    return markup_btns


def gen_order_ready_button(order_number: int) -> InlineKeyboardMarkup:
    markup_btn = InlineKeyboardMarkup()
    markup_btn.add(
        InlineKeyboardButton('Готов',
                             callback_data=order_callback_ready.new(order_number)),
    )
    return markup_btn


def gen_order_cancel_reasons_buttons(order_number: int) -> InlineKeyboardMarkup:
    markup_btns = InlineKeyboardMarkup(row_width=1)
    markup_btns.add(
        InlineKeyboardButton('Напиток и топинги не совместимы',
                             callback_data=order_cancel_reason.new(order_number, reason=CancelReasons.bad_mix)),
        InlineKeyboardButton('Нет напитка',
                             callback_data=order_cancel_reason.new(order_number, reason=CancelReasons.no_product)),
        InlineKeyboardButton('Нет топинга',
                             callback_data=order_cancel_reason.new(order_number, reason=CancelReasons.no_topping)),
        InlineKeyboardButton('Невозможно выполнить комментарий',
                             callback_data=order_cancel_reason.new(order_number, reason=CancelReasons.bad_comment)),
        InlineKeyboardButton('Не успеем приготовить',
                             callback_data=order_cancel_reason.new(order_number, reason=CancelReasons.zapara))
    )
    return markup_btns


def gen_bad_mix_button(order_number: int) -> InlineKeyboardMarkup:
    markup_btns = InlineKeyboardMarkup(row_width=1)
    db = SessionLocal()
    for prod in db.get(Order, order_number).ordered_products:
        markup_btns.add(InlineKeyboardButton(prod.product_various.product_various.name,
                                             callback_data=special_problem.new(order_number,
                                                                               prod.product_various.product_various.id,
                                                                               CancelReasons.bad_mix)))
    db.close()
    return markup_btns


def gen_no_product_button(order_number: int) -> InlineKeyboardMarkup:
    markup_btns = InlineKeyboardMarkup(row_width=1)
    db = SessionLocal()
    for prod in db.get(Order, order_number).ordered_products:
        markup_btns.add(InlineKeyboardButton(prod.product_various.product_various.name,
                                             callback_data=special_problem.new(order_number,
                                                                               prod.product_various.product_various.id,
                                                                               CancelReasons.no_product)))
    db.close()
    return markup_btns


def gen_no_topping_button(order_number: int) -> InlineKeyboardMarkup:
    markup_btns = InlineKeyboardMarkup(row_width=1)
    db = SessionLocal()
    for prod in db.get(Order, order_number).ordered_products:
        for top in prod.toppings:
            markup_btns.add(InlineKeyboardButton(top.topping.name,
                                                 callback_data=special_problem.new(order_number,
                                                                                   top.topping.id,
                                                                                   CancelReasons.no_topping)))
    db.close()

    return markup_btns
