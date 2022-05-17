from bot import bot
from telebot import types

from app.models import Customer
from bot.bot_funcs import send_bugreport_to_telegram, send_feedback_to_telegram


def change_user_name_state(message: types.Message, customer: Customer):
    new_name = message.text.strip()
    if not new_name:
        bot.send_message(chat_id=message.chat.id, text='Имя не может быть пустым.')
        bot.register_next_step_handler_by_chat_id(message.chat.id, change_user_name_state, customer)
        return
    if len(new_name) > 20:
        bot.send_message(chat_id=message.chat.id, text='Длина имени не должна превышать 20 символов.')
        bot.register_next_step_handler_by_chat_id(message.chat.id, change_user_name_state, customer)
        return

    customer.name = new_name
    customer.save()
    bot.send_message(chat_id=message.chat.id,
                     text=f'Имя пользователя обновлено.\nНовое имя пользователя: {customer.name}')


def bug_report_state(message):
    customer: Customer = Customer.get_or_none(Customer.telegram_id == message.from_user.id)
    send_bugreport_to_telegram(message.text.strip(), customer=customer)


def feed_back_state(message: types.Message):
    send_feedback_to_telegram(message.text.strip())


@bot.message_handler(commands=['change_name'], chat_types=['private'])
def handle_change_name_command(message):
    if customer := Customer.get_or_none(Customer.telegram_id == message.from_user.id):
        bot.send_message(message.chat.id, text='Введите новое имя (не более 20 символов):')
        bot.register_next_step_handler_by_chat_id(message.chat.id, change_user_name_state, customer)
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


@bot.message_handler(commands=['bug_report'], chat_types=['private'])
def handler_bug_report_command(message):
    bot.send_message(chat_id=message.chat.id, text='Введите ваше сообщение:')
    bot.register_next_step_handler_by_chat_id(message.chat.id, bug_report_state)


@bot.message_handler(commands=['feed_back'], chat_types=['private'])
def handler_feed_back_command(message):
    bot.send_message(chat_id=message.chat.id, text='Введите ваше сообщение:')
    bot.register_next_step_handler_by_chat_id(message.chat.id, feed_back_state)
