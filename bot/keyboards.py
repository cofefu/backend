from telebot import types

from bot.filters import order_callback_confirmed, order_callback_done, order_callback_ready


def gen_send_contact_button() -> types.ReplyKeyboardMarkup:
    btn = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn.add(
        types.KeyboardButton('Подтвердить номер телефона', request_contact=True)
    )
    return btn


def gen_order_done_buttons(order_number: int) -> types.InlineKeyboardMarkup:
    markup_btns = types.InlineKeyboardMarkup(row_width=2)
    markup_btns.add(
        types.InlineKeyboardButton('Выполнен',
                                   callback_data=order_callback_done.new(status=True, order_number=order_number)),
        types.InlineKeyboardButton('Не выполнен',
                                   callback_data=order_callback_done.new(status=False, order_number=order_number))
    )
    return markup_btns


def gen_order_confirmed_buttons(order_number: int) -> types.InlineKeyboardMarkup:
    markup_btns = types.InlineKeyboardMarkup(row_width=2)
    markup_btns.add(
        types.InlineKeyboardButton('Принять',
                                   callback_data=order_callback_confirmed.new(status=True, order_number=order_number)),
        types.InlineKeyboardButton('Отклонить',
                                   callback_data=order_callback_confirmed.new(status=False, order_number=order_number))
    )
    return markup_btns


def gen_order_ready_button(order_number: int) -> types.InlineKeyboardMarkup:
    markup_btn = types.InlineKeyboardMarkup()
    markup_btn.add(
        types.InlineKeyboardButton('Готов',
                                   callback_data=order_callback_ready.new(order_number=order_number)),
    )
    return markup_btn
