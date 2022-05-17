from bot import bot
from telebot import types

from app.models import Customer
from bot.bot_funcs import send_bugreport_to_telegram


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


@bot.message_handler(commands=['bug_report'], chat_types=['private'])
def handler_bug_report_back(message):
    customer: Customer = Customer.get_or_none(Customer.telegram_id == message.from_user.id)
    send_bugreport_to_telegram(message.text[12:], customer=customer)
