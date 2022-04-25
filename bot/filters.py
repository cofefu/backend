import telebot
from telebot import types, AdvancedCustomFilter
from telebot.callback_data import CallbackData, CallbackDataFilter

from bot import bot

order_callback_confirmed = CallbackData("status", "order_number", prefix="order_confirmed")
order_callback_done = CallbackData("status", "order_number", prefix='order_done')
order_callback_ready = CallbackData('order_number', prefix='order_ready')


class OrderStatusCallbackFilter(AdvancedCustomFilter):  # OrderConfirmedCallbackFilter
    key = 'order_status_config'

    def check(self, call: types.CallbackQuery, config: CallbackDataFilter):
        return config.check(query=call)


# class OrderDoneCallbackFilter(AdvancedCustomFilter):
#     key = 'order_done_config'
#
#     def check(self, call: types.CallbackQuery, config: CallbackDataFilter):
#         return config.check(query=call)
#
#
# class OrderReadyCallbackFilter(AdvancedCustomFilter):
#     key = 'order_ready_config'
#
#     def check(self, call: types.CallbackQuery, config: CallbackDataFilter):
#         return config.check(query=call)


def bind_bot_filters():
    bot.add_custom_filter(OrderStatusCallbackFilter())
    # bot.add_custom_filter(OrderDoneCallbackFilter())
    # bot.add_custom_filter(OrderReadyCallbackFilter())
