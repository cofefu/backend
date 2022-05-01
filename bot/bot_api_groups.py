from bot import bot
from bot.bot_funcs import gen_order_msg_text, notify_order_change
from bot.filters import order_callback_confirmed, order_callback_done, order_callback_ready, order_cancel_reason, \
    CancelReasons, special_problem
from bot.keyboards import gen_order_done_buttons, gen_order_ready_button, \
    gen_order_cancel_reasons_buttons, gen_bad_mix_button, gen_no_product_button, gen_no_topping_button
from telebot import types

from app.models import Order, Customer, CoffeeHouse, ban_customer, Product, OrderCancelReason, Topping

from datetime import datetime, timedelta


@bot.message_handler(commands=['status'], chat_types=['group'])
def get_order_status(message):
    if CoffeeHouse.get_or_none(CoffeeHouse.chat_id == message.chat.id):
        order = Order.get_or_none(Order.id == message.text.split()[1])
        if order is not None:
            bot.send_message(chat_id=message.chat.id, text=f'Статус заказа №{order.id}: {order.get_status_name()}')
        else:
            bot.send_message(chat_id=message.chat.id, text=f'Заказ с номером {message.text} не найден')


@bot.message_handler(commands=['open_cafe', 'close_cafe'], chat_types=['group'])
def open_or_close_cafe(message):
    house: CoffeeHouse = CoffeeHouse.get_or_none(CoffeeHouse.chat_id == message.chat.id)
    if house is None:
        bot.send_message(chat_id=message.chat.id, text='Кофейня не найдена.')
        return

    command = message.text.split()[0]
    house.is_open = (command == '/open_cafe')
    house.save()

    status = 'Открыта' if house.is_open else 'Закрыта'
    bot.send_message(chat_id=message.chat.id, text=f'Кофейня {house.name} в {house.placement}\n{status}')


@bot.message_handler(commands=['ban'], chat_types=['group'])
def ban_request(message):
    if not CoffeeHouse.get_or_none(CoffeeHouse.chat_id == message.chat.id):
        return

    phone_number = message.text.split()[1]
    customer: Customer = Customer.get_or_none(Customer.phone_number == phone_number[-10:])
    if customer is None:
        bot.send_message(chat_id=message.chat.id, text=f'Пользователь с номером телефона {phone_number} не найден')
        return

    ban = ban_customer(customer, datetime.utcnow() + timedelta(days=2))
    bot.send_message(chat_id=message.chat.id,
                     text=f'Пользователь {customer.name} с номером телефона {phone_number} ' +
                          f'забанен до {ban.expire.strftime("%d/%m/%Y, %H:%M")}')


@bot.message_handler(commands=['unban'], chat_types=['group'])
def unban_request(message):
    if not CoffeeHouse.get_or_none(CoffeeHouse.chat_id == message.chat.id):
        return
    phone_number = message.text.split()[1]
    customer: Customer = Customer.get_or_none(Customer.phone_number == phone_number[-10:])
    if customer is None:
        bot.send_message(chat_id=message.chat.id, text=f'Пользователь с номером телефона {phone_number} не найден')
        return

    if (ban := customer.ban) is not None:
        ban.delete_instance()
    bot.send_message(chat_id=message.chat.id,
                     text=f'Пользователь {customer.name} с номером телефона {phone_number} ' +
                          f'разбанен')


@bot.callback_query_handler(func=None, order_status_config=order_callback_confirmed.filter())
def callback_order_confirmed_handler(call: types.CallbackQuery):
    callback_data: dict = order_callback_confirmed.parse(callback_data=call.data)
    is_confirmed, order_number = int(callback_data['status']), int(callback_data['order_number'])

    order = Order.get_or_none(id=order_number)
    if order is None:
        bot.answer_callback_query(call.id, 'Заказ не найден')
        return
    order.status = 1 if is_confirmed else 2
    order.save()

    ans = 'Заказ принят' if is_confirmed else 'Выберете причины отмены заказа:'
    bot.answer_callback_query(call.id, ans)
    ans = f"\n<b>{ans}</b>"

    if is_confirmed:
        notify_order_change(order)
    markup = gen_order_ready_button(order.id) if is_confirmed else gen_order_cancel_reasons_buttons(order.id)
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=gen_order_msg_text(order.id) + ans,
                          parse_mode='HTML',
                          reply_markup=markup)


@bot.callback_query_handler(func=None, order_status_config=order_callback_ready.filter())
def callback_order_ready_handler(call: types.CallbackQuery):
    callback_data: dict = order_callback_ready.parse(callback_data=call.data)
    order_number = int(callback_data['order_number'])

    order = Order.get_or_none(id=order_number)
    if order is None:
        bot.answer_callback_query(call.id, 'Заказ не найден')
        return
    order.status = 5
    order.save()

    ans = 'Заказ готов'
    bot.answer_callback_query(call.id, ans)
    ans = f"\n<b>{ans}</b>"

    notify_order_change(order)
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=gen_order_msg_text(order.id) + ans,
                          parse_mode='HTML',
                          reply_markup=gen_order_done_buttons(order.id))


@bot.callback_query_handler(func=None, order_status_config=order_callback_done.filter())
def callback_order_confirmed_handler(call: types.CallbackQuery):
    callback_data: dict = order_callback_done.parse(callback_data=call.data)
    is_done, order_number = int(callback_data['status']), int(callback_data['order_number'])

    order = Order.get_or_none(id=order_number)
    if order is None:
        bot.answer_callback_query(call.id, 'Заказ не найден')
        return
    order.status = 3 if is_done else 4
    order.save()

    ans = 'Покупатель забрал заказ' if is_done else 'Покупатель не забрал заказ'
    bot.answer_callback_query(call.id, ans)
    ans = f"\n<b>{ans}</b>"

    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=gen_order_msg_text(order.id) + ans,
                          parse_mode='HTML',
                          reply_markup=None)


@bot.callback_query_handler(func=None, order_cancel_config=order_cancel_reason.filter())
def callback_order_cancel_reasons(call: types.CallbackQuery):
    callback_data: dict = order_cancel_reason.parse(callback_data=call.data)
    order_number, reason = int(callback_data['order_number']), int(callback_data['reason'])
    order = Order.get_or_none(id=order_number)
    if order is None:
        bot.answer_callback_query(call.id, 'Заказ не найден')
        return

    if reason == CancelReasons.bad_mix:
        bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      reply_markup=gen_bad_mix_button(order_number))
    elif reason == CancelReasons.no_product:
        bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      reply_markup=gen_no_product_button(order_number))
    elif reason == CancelReasons.no_topping:
        bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      reply_markup=gen_no_topping_button(order_number))
    elif reason == CancelReasons.bad_comment:
        ans = 'Заказ отклонен т.к. комментарий невыполним'
        msg = gen_order_msg_text(order_number) + f'\n<b>{ans}</b>'
        OrderCancelReason.create(order=order, reason=ans)
        notify_order_change(order)
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg,
                              parse_mode='HTML',
                              reply_markup=None)
        # 'Заказ отменен т.к. невозможно выполнить пожелания покупателя'
    elif reason == CancelReasons.zapara:
        ans = 'Заказ отклонен т.к мы не успеем приготовить его вовремя'
        msg = gen_order_msg_text(order_number) + f'\n<b>{ans}</b>'
        OrderCancelReason.create(order=order, reason=ans)
        notify_order_change(order)
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg,
                              parse_mode='HTML',
                              reply_markup=None)
    else:
        bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      reply_markup=None)


@bot.callback_query_handler(func=None, order_cancel_config=special_problem.filter())
def callback_order_bad_mix(call: types.CallbackQuery):
    cb_data: dict = special_problem.parse(callback_data=call.data)
    id_ = int(cb_data['id'])
    order_number = int(cb_data['order_number'])
    reason = int(cb_data['reason'])
    order = Order.get_or_none(id=order_number)
    if order is None:
        bot.answer_callback_query(call.id, 'Заказ не найден')
        return

    text = f'Заказ отклонен'
    if reason == CancelReasons.bad_mix:
        text = f'Заказ отклонен т.к. нельзя сочетать "{Product.get_by_id(id_).name}" с выбранными топингами'
    elif reason == CancelReasons.no_product:
        text = f'Заказ отклонен т.к. напиток "{Product.get_by_id(id_).name}" временно отсутствует'
    elif reason == CancelReasons.no_topping:
        text = f'Заказ отклонен т.к топинг "{Topping.get_by_id(id_).name}" временно отсутствует'

    OrderCancelReason.create(order=order, reason=text)
    notify_order_change(order)
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=gen_order_msg_text(order.id) + f'\n<b>{text}</b>',
                          parse_mode='HTML',
                          reply_markup=None)
