from datetime import datetime, timedelta

from fastapi import APIRouter
import telebot

from app.models import Order, Customer, CoffeeHouse, ban_customer, Product, OrderCancelReason, Topping
from backend.settings import DOMAIN, BOT_TOKEN, BOT_PORT, DEBUG, FEEDBACK_CHAT
from bot import bot
from telebot import types

from bot.bot_funcs import gen_order_msg_text, send_feedback_to_telegram, send_bugreport_to_telegram, notify_order_change
from bot.filters import order_callback_confirmed, order_callback_done, order_callback_ready, order_cancel_reason, \
    CancelReasons, special_problem
from bot.keyboards import gen_send_contact_button, gen_order_done_buttons, gen_order_ready_button, \
    gen_order_cancel_reasons_buttons, gen_bad_mix_button, gen_no_product_button, gen_no_topping_button

router = APIRouter()


def set_webhook():
    webhook_url = f"https://{DOMAIN}:{BOT_PORT}" + f'/bot/{BOT_TOKEN}/'
    if not DEBUG and \
            bot.get_webhook_info().url != webhook_url:
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)


def order_not_picked(order: Order):
    customer = order.customer
    if len(customer.customer_orders.where(Order.status == 4)) >= 3:
        ban_customer(customer, datetime.utcnow(), forever=True)


@router.post(f'/{BOT_TOKEN}/', include_in_schema=False)
def process_webhook(update: dict):
    if update:
        update = telebot.types.Update.de_json(update)
        bot.process_new_updates([update])
    else:
        return


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = gen_send_contact_button()
    if message.chat.type == 'group':
        markup = None
    bot.send_message(message.chat.id,
                     f"Hello, i'm cofefu webhook bot.",
                     reply_markup=markup)


@bot.message_handler(commands=['help'])
def send_help_info(message):
    msg = 'Команды:\n'
    if message.chat.type == 'group':
        msg += '<b>/status</b> НОМЕР_ЗАКАЗА - <i>чтобы узнать статус указанного заказа</i>\n'
    else:
        msg += '<b>/start</b> - <i>для подтверждения номера телефона</i>\n'
        msg += '<b>/change_name</b> ТЕКСТ - <i>для изменения имени пользователя</i>\n'
    msg += '<b>/bug_report</b> ТЕКСТ - <i>для информации о различных ошибках</i>\n'
    msg += '<b>/feed_back</b> ТЕКСТ - <i>для советов, пожеланий</i>'

    bot.send_message(chat_id=message.chat.id, text=msg, parse_mode='HTML')


@bot.message_handler(commands=['chat_id'])
def send_chat_id(message):
    bot.reply_to(message, message.chat.id)


@bot.message_handler(commands=['status'], chat_types=['group'])
def get_order_status(message):
    if CoffeeHouse.get_or_none(CoffeeHouse.chat_id == message.chat.id):
        order = Order.get_or_none(Order.id == message.text.split()[1])
        if order is not None:
            bot.send_message(chat_id=message.chat.id, text=f'Статус заказа №{order.id}: {order.get_status_name()}')
        else:
            bot.send_message(chat_id=message.chat.id, text=f'Заказ с номером {message.text} не найден')


@bot.message_handler(commands=['bug_report', 'feed_back'])
def send_bug_report(message):
    if message.text.split()[0] == '/feed_back':
        send_feedback_to_telegram(message.text[11:])
    else:
        send_bugreport_to_telegram(message.text[12:])


@bot.message_handler(commands=['change_name'], chat_types=['private'])
def change_user_name(message):
    if customer := Customer.get_or_none(Customer.telegram_id == message.from_user.id):
        new_name = message.text[13:].strip()
        if not new_name:
            bot.send_message(chat_id=message.chat.id,
                             text='Имя не может быть пустым.\nПример команды: /change_name Иван')
            return
        customer.name = new_name
        customer.save()

        bot.send_message(chat_id=message.chat.id,
                         text=f'Имя пользователя обновлено.\nНовое имя пользователя: {customer.name}')
    else:
        bot.send_message(chat_id=message.chat.id,
                         text='Пользователь не найден. Пожалуйста, еще раз подтвердите номер телефона (команда /start)')


@bot.message_handler(content_types=['contact'], chat_types=['private'])
def contact_handler(message):
    phone_number = message.contact.phone_number
    if message.contact.user_id != message.from_user.id:
        bot.send_message(chat_id=message.chat.id,
                         text='Это НЕ ваш номер телефона.')
        return

    if customer := Customer.get_or_none(Customer.phone_number == phone_number[-10:]):
        customer.confirmed = True
        customer.chat_id = message.chat.id
        customer.telegram_id = message.from_user.id
        customer.save()

        bot.send_message(chat_id=message.chat.id,
                         text='Номер телефона подтвержден.',
                         reply_markup=types.ReplyKeyboardRemove(
                             selective=False))
    else:
        bot.send_message(chat_id=message.chat.id,
                         text='Пользователь с таким номером телефона не найден.')


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
        msg = gen_order_msg_text(order_number) + f'\n<b>ans</b>'
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
