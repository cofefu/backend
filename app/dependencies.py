from datetime import datetime

from fastapi import Depends, Header, HTTPException, status
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.orm import Session

from app.models import Customer, Order

from db import SessionLocal
from fastapiProject.settings import settings


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def decode_jwt_token(jwt_token: str = Header(...)) -> dict:
    try:
        return jwt.decode(jwt_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Срок действия токена истек.')
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Не удалось проверить учетные данные.')


def get_current_user(data: dict = Depends(decode_jwt_token), db: Session = Depends(get_db)) -> Customer:
    phone_number = data.get("sub")
    if phone_number is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Отсутствуют необходимые поля.')

    customer: Customer = db.query(Customer).filter_by(phone_number=phone_number).one_or_none()
    if customer is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Пользователь с таким номером телефона отсутствует.')
    return customer


def get_current_active_user(customer: Customer = Depends(get_current_user)) -> Customer:
    if not customer.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Номер телефона не подтвержден.')
    return customer


def get_not_baned_user(customer: Customer = Depends(get_current_active_user)) -> Customer:
    ban = customer.ban
    if ban is None:
        return customer
    if ban.forever or datetime.utcnow() <= ban.expire:
        raise HTTPException(status_code=status.HTTP_412_PRECONDITION_FAILED,
                            detail='Данный пользователь находится в черном списке')
    return customer


def timeout_is_over(customer: Customer = Depends(get_current_active_user), db: Session = Depends(get_db)):
    last_order: Order = (db.query(Order)
                         .filter_by(customer_id=customer.id)
                         .join(Customer)
                         .order_by(Order.id.desc())
                         .first())
    if last_order is None:
        return

    if datetime.utcnow() - last_order.creation_time <= settings.order_timeout:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                            detail=f'С момента последнего заказа прошло менее 2 минут')
