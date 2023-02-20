from enum import Enum

import telebot
from telebot import types, AdvancedCustomFilter
from telebot.callback_data import CallbackData, CallbackDataFilter

from app.models import FSM
from bot import bot
from db import SessionLocal
from sqlalchemy.orm import Session

order_callback_confirmed = CallbackData("order_number", "status", prefix="order_confirmed")
order_callback_done = CallbackData("order_number", "status", prefix='order_done')
order_callback_ready = CallbackData('order_number', prefix='order_ready')

order_cancel_reason = CallbackData('order_number', 'reason', prefix='order_cancel')
special_problem = CallbackData('order_number', 'id', 'reason', prefix='cancel_product_reasons')


# reason_bad_mix = CallbackData('order_number', 'product_id', prefix='bad_mix')
# reason_no_product = CallbackData('order_number', 'product_id', prefix='no_product')
# reason_no_topping = CallbackData('order_number', 'topping_id', prefix='no_topping')


class CancelReasons:
    bad_mix = 0
    no_product = 1
    no_topping = 2
    bad_comment = 3
    zapara = 4


class States:
    changing_name = 0
    sending_feedback = 1
    bug_report_request_contact = 2
    sending_bugreport_with_contact = 3
    sending_bugreport_without_contact = 4


class OrderStatusCallbackFilter(AdvancedCustomFilter):
    key = 'order_status_config'

    def check(self, call: types.CallbackQuery, config: CallbackDataFilter):
        return config.check(query=call)


class OrderCancelCallbackFilter(AdvancedCustomFilter):
    key = 'order_cancel_config'

    def check(self, call: types.CallbackQuery, config: CallbackDataFilter):
        return config.check(query=call)


class FSMFilter(AdvancedCustomFilter):
    key = 'state'

    def check(self, message: types.Message, state):
        with SessionLocal() as db:
            db: Session
            if fsm := db.query(FSM).filter_by(telegram_id=message.from_user.id).first():
                return fsm.state == state
            return False


def bind_bot_filters():
    bot.add_custom_filter(OrderStatusCallbackFilter())
    bot.add_custom_filter(OrderCancelCallbackFilter())
    bot.add_custom_filter(FSMFilter())
