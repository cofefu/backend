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
SERVER_PORT = 80

API_TOKEN = os.getenv('API_TOKEN')
DOMAIN = os.getenv('DOMAIN')

WEBHOOK_SSL_CERT = '/etc/nginx/ssl/cert.pem'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = '/etc/nginx/ssl/pkey.pem'  # Path to the ssl private key

EMAIL_USER_LOGIN = 'coffefuorder@mail.ru'
EMAIL_USER_PASSWORD = os.getenv('EMAIL_USER_PASSWORD')
EMAIL_SERVER = 'smtp.mail.ru'
