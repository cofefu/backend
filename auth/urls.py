from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import Customer, LoginCode
from auth.dependencies import get_current_user, get_current_active_user
from auth.schemas import CustomerCreate, CustomerResponse, CustomerNewName
from auth.services import create_token, gen_login_code, min_lifetime_login_code
from bot.services import send_login_code_to_telegram

router = APIRouter(prefix='/api')


@router.post('/register_customer',
             tags=['auth'],
             description='Служит для создание аккаунта покупателя',
             response_description="Возвращает jwt-токен customer'а")
async def register_customer(
        customer: Annotated[CustomerCreate, Body()],
        db: Annotated[Session, Depends(get_db)]):
    if db.query(Customer).get(customer.phone_number):
        raise HTTPException(status_code=400,
                            detail='Пользователь с таким номером телефона уже существует.')

    new_customer = Customer(name=customer.name, phone_number=customer.phone_number)
    new_customer.save(db)
    return create_token(new_customer)


@router.post('/update_token',
             tags=['jwt require', 'auth'],
             description='Служит для обновления токена',
             response_description='Возвращает обновленный jwt-токен')
async def update_token(
        customer: Annotated[Customer, Depends(get_current_user)]):
    return create_token(customer)


@router.post('/send_login_code',
             tags=['auth'],
             description='Отправляет пользователю код для подтверждения входа',
             response_description='Ничего не возвращает')
async def send_login_code(
        phone_number: Annotated[int, Body(embed=True)],
        background_tasks: BackgroundTasks,
        db: Annotated[Session, Depends(get_db)]):
    customer: Customer = db.query(Customer).get(phone_number)
    if customer is None:
        raise HTTPException(status_code=400,
                            detail='Пользователя с таким номером телефона не существует.')
    if customer.telegram_id is None:
        raise HTTPException(status_code=401, detail='Номер телефона не подтвержден.')

    lc = LoginCode(
        code=gen_login_code(db),
        customer_phone_number=customer.phone_number,
        expire=datetime.utcnow() + min_lifetime_login_code()
    )
    lc.save(db)
    background_tasks.add_task(send_login_code_to_telegram, lc)
    return "Success"


@router.get('/verify_login_code',
            tags=['auth'],
            description='Для проверки login кода и получения jwt-токена',
            response_description='Возвращает jwt-токен')
async def verify_login_code(
        code: Annotated[int, Query()],
        background_tasks: BackgroundTasks,
        db: Annotated[Session, Depends(get_db)]):
    login_code: LoginCode = db.query(LoginCode).get(code)
    if login_code is None:
        raise HTTPException(status_code=401, detail='Неверный код подтверждения.')
    if login_code.expire < datetime.utcnow():
        raise HTTPException(status_code=401, detail='Срок действия кода подтверждения истек.')

    background_tasks.add_task(login_code.delete, db)
    return create_token(login_code.customer)


@router.get('/is_confirmed',
            tags=['jwt require', 'auth'],
            description='Возвращает ошибку, если номер не подтвержден')
async def get_user_is_confirmed(
        customer: Annotated[Customer, Depends(get_current_active_user)]):
    return "Success"


@router.put('/change_name',
            tags=['jwt require', 'auth'],
            description='Для смены имени пользователя',
            response_model=CustomerResponse)
async def change_customer_name(
        new_name_model: Annotated[CustomerNewName, Body()],
        customer: Annotated[Customer, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)]):
    customer.name = new_name_model.new_name
    customer.save(db)
    return customer.data()


@router.get('/me',
            tags=['jwt require', 'auth'],
            description='Возвращает информацию о текущем пользователе',
            response_model=CustomerResponse)
async def get_me(
        customer: Annotated[Customer, Depends(get_current_user)]):
    return customer.data()
