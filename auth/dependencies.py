from datetime import datetime
from typing import Annotated

from fastapi import Header, HTTPException, status, Depends
from jose import jwt, ExpiredSignatureError, JWTError
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import Customer
from fastapiProject.settings import settings


def decode_jwt_token(
        jwt_token: Annotated[str, Header(...)]
) -> dict:
    try:
        return jwt.decode(jwt_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Срок действия токена истек.')
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Не удалось проверить учетные данные.')


def get_current_user(
        jwt_data: Annotated[dict, Depends(decode_jwt_token)],
        db: Annotated[Session, Depends(get_db)]
) -> Customer:
    phone_number = jwt_data.get("sub")
    if phone_number is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Отсутствуют необходимые поля.')

    customer: Customer = db.query(Customer).get(phone_number)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Пользователь с таким номером телефона отсутствует.')
    return customer


def get_current_active_user(
        customer: Annotated[Customer, Depends(get_current_user)]
) -> Customer:
    if not customer.telegram_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Номер телефона не подтвержден.')
    return customer


def get_not_baned_user(
        customer: Annotated[Customer, Depends(get_current_active_user)]
) -> Customer:
    ban = customer.ban
    if ban is None:
        return customer
    if ban.forever or datetime.utcnow() <= ban.expire:
        raise HTTPException(status_code=status.HTTP_412_PRECONDITION_FAILED,
                            detail='Данный пользователь находится в черном списке')
    return customer
