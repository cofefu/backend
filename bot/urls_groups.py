from sqlalchemy.orm import Session

from bot import bot
from bot.bot_funcs import gen_order_msg_text, notify_order_change, send_bugreport_to_telegram
from bot.filters import order_callback_confirmed, order_callback_done, order_callback_ready, order_cancel_reason, \
    CancelReasons, special_problem
from bot.keyboards import gen_order_done_buttons, gen_order_ready_button, \
    gen_order_cancel_reasons_buttons, gen_bad_mix_button, gen_no_product_button, gen_no_topping_button
from telebot import types

from app.models import Order, Customer, CoffeeHouse, ban_customer, Product, OrderCancelReason, Topping, OrderStatuses

from datetime import datetime, timedelta

from db import SessionLocal


@bot.message_handler(commands=['help'], chat_types=['group', 'supergroup'])
def send_help_info(message):
    msg = 'Команды:\n'
    msg += '<b>/open_cafe</b> - <i>чтобы открыть кафе в особых случаях</i>\n'
    msg += '<b>/close_cafe</b> - <i>чтобы закрыть кафе в особых случаях</i>\n'
    msg += '<b>/ban</b> НОМЕР_ТЕЛЕФОНА - <i>чтобы забанить пользователя на 2 дня</i>\n'
    msg += '<b>/unban</b> НОМЕР_ТЕЛЕФОНА - <i>чтобы разбанить пользователя</i>\n'

    bot.send_message(chat_id=message.chat.id, text=msg, parse_mode='HTML')


@bot.message_handler(commands=['status'], chat_types=['group', 'supergroup'])
def get_order_status(message):
    db = SessionLocal()
    if db.query(CoffeeHouse).filter_by(chat_id=message.chat.id).first():
        order: Order = db.get(Order, message.text.split()[1])
        if order is not None:
            bot.send_message(chat_id=message.chat.id, text=f'Статус заказа №{order.id}: {order.get_status_name()}')
        else:
            bot.send_message(chat_id=message.chat.id, text=f'Заказ с номером {message.text} не найден')
    db.close()


@bot.message_handler(commands=['open_cafe', 'close_cafe'], chat_types=['group', 'supergroup'])
def open_or_close_cafe(message):
    db: Session
    with SessionLocal() as db:
        house: CoffeeHouse
        if house := db.query(CoffeeHouse).filter_by(chat_id=message.chat.id).first() is None:
            bot.send_message(chat_id=message.chat.id, text='Кофейня не найдена.')
            return

        command = message.text.split()[0]
        house.is_open = (command == '/open_cafe')
        db.commit()

        status = 'Открыта' if house.is_open else 'Закрыта'
        bot.send_message(chat_id=message.chat.id, text=f'Кофейня {house.name} в {house.placement}\n{status}')


@bot.message_handler(commands=['ban'], chat_types=['group', 'supergroup'])
def ban_request(message):
    db: Session
    with SessionLocal() as db:
        if db.query(CoffeeHouse).filter_by(chat_id=message.chat.id).first() is None:
            return

        phone_number = message.text.split()[1]
        customer: Customer
        if customer := db.query(Customer).filter_by(phone_number=phone_number[-10:]).first() is None:
            bot.send_message(chat_id=message.chat.id, text=f'Пользователь с номером телефона {phone_number} не найден')
            return

        ban = ban_customer(customer, datetime.utcnow() + timedelta(days=2))
        bot.send_message(chat_id=message.chat.id,
                         text=f'Пользователь {customer.name} с номером телефона {phone_number} ' +
                              f'забанен до {ban.expire.strftime("%d/%m/%Y, %H:%M")}')


@bot.message_handler(commands=['unban'], chat_types=['group', 'supergroup'])
def unban_request(message):
    db: Session
    with SessionLocal() as db:
        if db.query(CoffeeHouse).filter_by(chat_id=message.chat.id).first() is None:
            return
        phone_number = message.text.split()[1]
        customer: Customer
        if customer := db.query(Customer).filter_by(phone_number=phone_number[-10:]).first() is None:
            bot.send_message(chat_id=message.chat.id, text=f'Пользователь с номером телефона {phone_number} не найден')
            return

        if (ban := customer.ban) is not None:
            db.delete(ban)
            db.commit()
        bot.send_message(chat_id=message.chat.id,
                         text=f'Пользователь {customer.name} с номером телефона {phone_number} ' +
                              f'разбанен')


@bot.callback_query_handler(func=None, order_status_config=order_callback_confirmed.filter())
def callback_order_confirmed_handler(call: types.CallbackQuery):
    callback_data: dict = order_callback_confirmed.parse(callback_data=call.data)
    is_confirmed, order_number = int(callback_data['status']), int(callback_data['order_number'])

    db: Session
    with SessionLocal() as db:
        order: Order = db.get(Order, order_number)
        if order is None:
            bot.answer_callback_query(call.id, 'Заказ не найден')
            return
        order.status = OrderStatuses.accepted if is_confirmed else OrderStatuses.rejected
        db.commit()

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

    db: Session
    with SessionLocal() as db:
        order: Order = db.get(Order, order_number)
        if order is None:
            bot.answer_callback_query(call.id, 'Заказ не найден')
            return
        order.status = OrderStatuses.ready
        db.commit()

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
def callback_order_done_handler(call: types.CallbackQuery):
    callback_data: dict = order_callback_done.parse(callback_data=call.data)
    is_done, order_number = int(callback_data['status']), int(callback_data['order_number'])

    db: Session
    with SessionLocal() as db:
        order: Order = db.get(Order, order_number)
        if order is None:
            bot.answer_callback_query(call.id, 'Заказ не найден')
            return
        order.status = OrderStatuses.taken if is_done else OrderStatuses.no_taken
        db.commit()

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

    db: Session = SessionLocal()
    order: Order = db.get(Order, order_number)
    if order is None:
        bot.answer_callback_query(call.id, 'Заказ не найден')
        db.close()
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
        db.add(OrderCancelReason(order_id=order.id, reason=ans))
        db.commit()
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
        db.add(OrderCancelReason(order_id=order.id, reason=ans))
        db.commit()
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
    db.close()


@bot.callback_query_handler(func=None, order_cancel_config=special_problem.filter())
def callback_order_bad_mix(call: types.CallbackQuery):
    db: Session = SessionLocal()
    cb_data: dict = special_problem.parse(callback_data=call.data)
    prod_id = int(cb_data.get('id'))
    order_number = int(cb_data.get('order_number'))
    reason = int(cb_data.get('reason'))
    order: Order = db.get(Order, order_number)
    if order is None:
        bot.answer_callback_query(call.id, 'Заказ не найден')
        db.close()
        return

    if reason == CancelReasons.bad_mix:
        text = f'Заказ отклонен т.к. нельзя сочетать "{db.get(Product, prod_id).name}" с выбранными топингами'
    elif reason == CancelReasons.no_product:
        text = f'Заказ отклонен т.к. напиток "{db.get(Product, prod_id).name}" временно отсутствует'
    elif reason == CancelReasons.no_topping:
        text = f'Заказ отклонен т.к топинг "{db.get(Product, prod_id).name}" временно отсутствует'
    else:
        text = f'Заказ отклонен'

    db.add(OrderCancelReason(order_id=order.id, reason=text))
    db.commit()
    notify_order_change(order)
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=gen_order_msg_text(order.id) + f'\n<b>{text}</b>',
                          parse_mode='HTML',
                          reply_markup=None)
    db.close()
