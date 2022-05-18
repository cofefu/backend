import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

APPS = (
    'app',
    'bot',
)

DEBUG = bool(os.getenv("DEBUG", False))
DEV = bool(os.getenv("DEV", False))

DATABASE = {
    'NAME': os.getenv('DB_NAME'),
    'USER': os.getenv('DB_USER'),
    'PASSWORD': os.getenv('DB_PASSWORD'),
}

SERVER_HOST = os.getenv('SERVER_HOST', 'localhost')
SERVER_PORT = int(os.getenv('SERVER_PORT', 8000))
ALLOW_ORIGINS = [
    'https://cofefu.ru'
] if not (DEV or DEBUG) else ['*']

BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_PORT = os.getenv('BOT_PORT', 443)
FEEDBACK_CHAT = os.getenv('FEEDBACK_CHAT')
DOMAIN = os.getenv('DOMAIN')

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_ALGORITHM = "HS256"

WORKERS = int(os.getenv('WORKERS', 1))
API_PREFIX = '/dev' if DEV else ''

ORDER_TIMEOUT = timedelta() if (DEV or DEBUG) else timedelta(minutes=2)
