from sqlalchemy.orm import Session

from bot import bot
from telebot import types

from app.models import Customer, FSM, get_or_create
from bot.services import send_bugreport_to_telegram, send_feedback_to_telegram
from bot.filters import States
from db import SessionLocal


@bot.message_handler(commands=['help'], chat_types=['private'])
def send_help_info(message):
    msg = 'Команды:\n'
    msg += '<b>/start</b> - <i>для подтверждения номера телефона</i>\n'
    msg += '<b>/change_name</b> - <i>для изменения имени пользователя</i>\n'
    msg += '<b>/bug_report</b> - <i>для информации о различных ошибках</i>\n'
    msg += '<b>/feed_back</b> - <i>для советов, пожеланий ;)</i>'

    bot.send_message(chat_id=message.chat.id, text=msg, parse_mode='HTML')


@bot.message_handler(content_types=['contact'], chat_types=['private'])
def contact_handler(message):
    phone_number = message.contact.phone_number
    if message.contact.user_id != message.from_user.id:
        bot.send_message(chat_id=message.chat.id,
                         text='Это НЕ ваш номер телефона.')
        return

    db: Session = SessionLocal()
    customer: Customer
    if customer := db.query(Customer).get(phone_number[-10:]) is None:
        customer.chat_id = message.chat.id
        customer.telegram_id = message.from_user.id
        db.commit()

        bot.send_message(chat_id=message.chat.id,
                         text='Номер телефона подтвержден.',
                         reply_markup=types.ReplyKeyboardRemove(selective=False))
    else:
        bot.send_message(chat_id=message.chat.id,
                         text='Пользователь с таким номером телефона не найден.')
    db.close()


@bot.message_handler(commands=['change_name'], chat_types=['private'])
def handle_change_name_command(message):
    db: Session = SessionLocal()
    if db.query(Customer).filter_by(telegram_id=message.from_user.id).first():
        fsm: FSM = get_or_create(db, FSM, telegram_id=message.from_user.id)[0]
        fsm.state = States.changing_name
        db.commit()
        bot.send_message(message.chat.id, text='Введите новое имя (не более 20 символов):')
    else:
        bot.send_message(chat_id=message.chat.id,
                         text='Пользователь не найден. Пожалуйста, еще раз подтвердите номер телефона (команда /start)')
    db.close()


@bot.message_handler(commands=['bug_report'], chat_types=['private'])
def handler_bug_report_command(message: types.Message):
    db: Session = SessionLocal()
    fsm: FSM = get_or_create(db, FSM, telegram_id=message.from_user.id)[0]
    if db.query(Customer).filter_by(telegram_id=message.from_user.id).first():
        fsm.state = States.bug_report_request_contact
        db.commit()

        markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
        markup.add(types.KeyboardButton('Да'))
        markup.add(types.KeyboardButton('Нет'))
        bot.send_message(chat_id=message.chat.id,
                         reply_markup=markup,
                         text='Отправить контактные данные для обратной связи?')
    else:
        fsm.state = States.sending_bugreport_without_contact
        db.commit()
        bot.send_message(chat_id=message.chat.id, text='Введите ваше сообщение:')
    db.close()


@bot.message_handler(commands=['feed_back'], chat_types=['private'])
def handler_feed_back_command(message):
    db: Session = SessionLocal()
    fsm: FSM = FSM.get_or_create(telegram_id=message.from_user.id)[0]
    fsm.state = States.sending_feedback
    fsm.save()
    bot.send_message(chat_id=message.chat.id, text='Введите ваше сообщение:')
    db.close()


@bot.message_handler(func=lambda m: True, chat_types=['private'], state=States.changing_name)
def change_user_name_state(message: types.Message):
    db: Session
    with SessionLocal() as db:
        customer: Customer = db.query(Customer).filter_by(telegram_id=message.from_user.id).first()
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
        db.commit()
        fsm: FSM = db.query(FSM).filter_by(telegram_id=message.from_user.id)
        fsm.state = None
        db.commit()
        bot.send_message(chat_id=message.chat.id,
                         text=f'Имя пользователя обновлено.\nНовое имя пользователя: {customer.name}')


@bot.message_handler(func=lambda m: True, chat_types=['private'], state=States.sending_feedback)
def feed_back_state(message: types.Message):
    db: Session = SessionLocal()
    fsm: FSM = db.query(FSM).filter_by(telegram_id=message.from_user.id)
    fsm.state = None
    db.commit()
    send_feedback_to_telegram(message.text.strip())
    db.close()


@bot.message_handler(func=lambda m: True, chat_types=['private'], state=States.bug_report_request_contact)
def send_contact_state(message: types.Message):
    db: Session = SessionLocal()
    fsm: FSM = get_or_create(db, FSM, telegram_id=message.from_user.id)[0]
    if message.text.lower() == 'да':
        fsm.state = States.sending_bugreport_with_contact
    else:
        fsm.state = States.sending_bugreport_without_contact
    db.commit()
    db.close()
    bot.send_message(message.chat.id, text='Введите ваше сообщение:', reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(func=lambda m: True, chat_types=['private'], state=States.sending_bugreport_with_contact)
def bug_report_state(message: types.Message):
    db: Session = SessionLocal()
    fsm: FSM = db.query(FSM).filter_by(telegram_id=message.from_user.id).first()
    fsm.state = None
    db.commit()
    customer = db.query(Customer).filter_by(telegram_id=message.from_user.id).first()
    send_bugreport_to_telegram(message.text.strip(), customer=customer)
    db.close()


@bot.message_handler(func=lambda m: True, chat_types=['private'], state=States.sending_bugreport_without_contact)
def bug_report_state(message: types.Message):
    db: Session = SessionLocal()
    fsm: FSM = db.query(FSM).filter_by(telegram_id=message.from_user.id).first()
    fsm.state = None
    db.commit()
    db.close()
    send_bugreport_to_telegram(message.text.strip())
