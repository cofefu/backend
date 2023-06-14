import random

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Body
from pydantic import constr
from sqlalchemy.orm import Session
from starlette.responses import FileResponse
from jose import jwt
from datetime import datetime, timedelta

from app.models import Customer, LoginCode
from fastapiProject import schemas
from fastapiProject.settings import settings
from bot.bot_funcs import send_login_code, send_feedback_to_telegram, send_bugreport_to_telegram
from app.dependencies import get_current_user, get_db

router = APIRouter(prefix='/api')


def create_token(customer: Customer) -> str:
    user_data = {
        "sub": str(customer.phone_number),
        "exp": datetime.utcnow() + timedelta(days=14)
    }
    return jwt.encode(user_data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


# TEST return svg or ico depending on the user's browser
@router.get('/favicon.svg',
            description='Возвращает логотип в формате .svg',
            response_class=FileResponse)
async def get_favicon_svg():
    return FileResponse('assets/beans.svg')


@router.get('/favicon.ico',
            description='Возвращает логотип в формате .ico',
            response_class=FileResponse)
async def get_favicon_svg():
    return FileResponse('assets/beans.ico')


@router.post('/register_customer',
             description='Служит для создание аккаунта покупателя',
             response_description="Возвращает jwt-токен customer'а")
async def register_customer(customer: schemas.Customer, db: Session = Depends(get_db)):
    if db.query(Customer).filter_by(phone_number=customer.phone_number).one_or_none():
        raise HTTPException(status_code=400,
                            detail='Пользователь с таким номером телефона уже существует.')

    new_customer = Customer(name=customer.name, phone_number=customer.phone_number)
    new_customer.save(db)
    return create_token(new_customer)


@router.post('/update_token',
             tags=['jwt require'],
             description='Служит для обновления токена',
             response_description='Возвращает обновленный jwt-токен')
async def update_token(customer: Customer = Depends(get_current_user)):
    return create_token(customer)


@router.post('/send_login_code',
             description='Отправляет пользователю код для подтверждения входа',
             response_description='Ничего не возвращает')
async def create_login_code(customer_data: schemas.Customer,  # todo change to phone_number
                            background_tasks: BackgroundTasks,
                            db: Session = Depends(get_db)):
    customer = db.query(Customer).filter_by(phone_number=customer_data.phone_number).one_or_none()
    if customer is None:
        raise HTTPException(status_code=400,
                            detail='Пользователя с таким номером телефона не существует.')
    if not customer.confirmed:
        raise HTTPException(status_code=401, detail='Номер телефона не подтвержден.')

    code = random.randint(100000, 999999)
    while db.query(LoginCode).filter_by(code=code).one_or_none():
        code = random.randint(100000, 999999)

    lc_data = {
        "customer": customer,
        "code": code,
        "expire": datetime.utcnow() + timedelta(minutes=5)
    }
    lc = LoginCode(**lc_data)
    lc.save(db)
    background_tasks.add_task(send_login_code, lc)
    return "Success"


# TEST db.get(User, id) - instance or None
# TEST verify_lc
@router.get('/verify_login_code',
            description='Для проверки login кода и получения jwt-токена',
            response_description='Возвращает jwt-токен')
async def verify_login_code(code: int, db: Session = Depends(get_db)):
    login_code: LoginCode = db.query(LoginCode).filter_by(code=code).one_or_none()
    if login_code is None:
        raise HTTPException(status_code=401, detail='Неверный код подтверждения.')
    if login_code.expire < datetime.utcnow():
        raise HTTPException(status_code=401, detail='Срок действия кода подтверждения истек.')

    return create_token(login_code.customer)


@router.get('/me',
            tags=['jwt require'],
            description='Возвращает информацию о текущем пользователе',
            response_model=schemas.Customer)
async def get_me(customer: Customer = Depends(get_current_user)):
    return customer.data()


@router.post('/feedback', description='Для советов, пожеланий и т.д.')
async def send_feedback(background_tasks: BackgroundTasks, msg: str = Body(...)):
    background_tasks.add_task(send_feedback_to_telegram, msg)


@router.post('/bugreport',
             tags=['jwt require'],
             description='Для информации о различных ошибках')
async def send_bugreport(background_tasks: BackgroundTasks,
                         msg: str = Body(...),
                         customer: Customer = Depends(get_current_user)):
    background_tasks.add_task(send_bugreport_to_telegram, msg, customer)


@router.put('/change_name',
            tags=['jwt require'],
            description='Для смены имени пользователя',
            response_model=schemas.Customer)
async def change_customer_name(new_name: constr(strip_whitespace=True) = Body(...),
                               customer: Customer = Depends(get_current_user),
                               db: Session = Depends(get_db)):
    if len(new_name) > 20:
        raise HTTPException(status_code=422, detail='Длина имени не может превышать 20 символов')
    customer.name = new_name
    customer.save(db)
    return customer.data()


@router.get('/is_confirmed',
            tags=['jwt require'],
            description='Узнать подтвержден ли номер телефона')
async def get_user_is_confirmed(customer: Customer = Depends(get_current_user)):
    return bool(customer.confirmed)
