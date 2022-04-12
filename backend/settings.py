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
SERVER_PORT = 443

API_TOKEN = os.getenv('API_TOKEN')
DOMAIN = os.getenv('DOMAIN')

WEBHOOK_SSL_CERT = '/etc/nginx/ssl/cofefu.ru.cert'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = '/etc/nginx/ssl/pkey.pem'  # Path to the ssl private key

EMAIL_USER_LOGIN = 'coffefuorder@mail.ru'
EMAIL_USER_PASSWORD = os.getenv('EMAIL_USER_PASSWORD')
EMAIL_SERVER = 'smtp.mail.ru'

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_ALGORITHM = "HS256"
