from fastapi import Depends, Header, HTTPException, status
from jose import jwt, JWTError, ExpiredSignatureError

from app.models import Customer
from backend.settings import JWT_SECRET_KEY, JWT_ALGORITHM


def decode_jwt_token(jwt_token: str = Header(...)) -> dict:
    try:
        return jwt.decode(jwt_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Срок действия токена истек.')
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Не удалось проверить учетные данные.')


def get_current_user(data: dict = Depends(decode_jwt_token)) -> Customer:
    phone_number = data.get("sub")
    if phone_number is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Отсутствуют необходимые поля.')

    customer: Customer = Customer.get_or_none(Customer.phone_number=phone_number)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Пользователь с таким номером телефона отсутствует.')
    return customer


def get_current_active_user(customer: Customer = Depends(get_current_user)) -> Customer:
    if not customer.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Пользователь не подтвердил номер телефона.')
    return customer
