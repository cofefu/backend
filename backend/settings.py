import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE = {
    'NAME': 'coffefu.db',
    'USER': 'admin',
    'PASSWORD': '123',
}

SERVER_HOST = os.getenv('SERVER_HOST', 'localhost')
SERVER_PORT = os.getenv('SERVER_PORT', 8000)

BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_PORT = os.getenv('BOT_PORT', 443)
DOMAIN = os.getenv('DOMAIN')

EMAIL_USER_LOGIN = 'coffefuorder@mail.ru'
EMAIL_USER_PASSWORD = os.getenv('EMAIL_USER_PASSWORD')
EMAIL_SERVER = 'smtp.mail.ru'

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_ALGORITHM = "HS256"
