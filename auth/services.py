import random
from datetime import timedelta, datetime

from jose import jwt
from sqlalchemy.orm import Session

from db.models import LoginCode, Customer
from config.settings import settings


def create_token(
        customer: Customer
) -> str:
    """
    Создает и возвращает jwt-токен для пользователя с временем жизни 14 дней
    :param customer: Customer db model
    :return: jwt token
    """
    user_data = {
        "sub": str(customer.phone_number),
        "exp": datetime.utcnow() + timedelta(days=14)
    }
    return jwt.encode(user_data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def gen_login_code(
        db: Session
) -> int:
    """
    Генерирует уникальный 6-ти значный код для входа.
    :param db: Sqlalchemy session
    :return: integer code
    """
    code = random.randint(100000, 999999)
    while db.query(LoginCode).get(code):
        code = random.randint(100000, 999999)
    return code


def min_lifetime_login_code() -> timedelta:
    """
    :return: min lifetime login code :)
    """
    return timedelta(minutes=5)
