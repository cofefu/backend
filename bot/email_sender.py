import smtplib
from email.utils import formataddr
from email.message import EmailMessage

# from backend.settings import EMAIL_USER_LOGIN, EMAIL_USER_PASSWORD, EMAIL_SERVER

EMAIL_USER_LOGIN = ''
EMAIL_USER_PASSWORD = ''
EMAIL_SERVER = ''

# https://www.youtube.com/watch?v=700lW07627Y - краткое руководство
# https://sendpulse.com/ru/blog/how-to-create-avatar-for-email - для аватарки

sender = EMAIL_USER_LOGIN
sender_password = EMAIL_USER_PASSWORD
sender_name = 'Приложение Coffefu'


def send_email(customer: str, order_number: int, status: bool):
    msg_theme = 'Заказ принят' if status else 'Заказ отклонен'
    msg_text = f'Ваш заказ №{order_number} '
    msg_text += 'принят в работу.☺' if status else 'отклонен.😧'
    msg_text += '\n\nХорошего дня.'
    recipient = [customer]

    msg = EmailMessage()
    msg.set_content(msg_text)
    msg['Subject'] = msg_theme
    msg['From'] = formataddr((sender_name, sender))
    msg['To'] = ', '.join(recipient)

    server = smtplib.SMTP_SSL(EMAIL_SERVER, 465)
    server.login(sender, sender_password)
    server.send_message(msg)

    server.quit()
