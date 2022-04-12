import random
from typing import List

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from starlette.responses import FileResponse
from jose import jwt
from datetime import datetime, timedelta

from app.models import ProductVarious, Product, Topping, CoffeeHouse, Customer, Order, OrderedProduct, \
    ToppingToProduct, LoginCode
from backend import schemas
from backend.schemas import CoffeeHouseResponseModel, ProductsVariousResponseModel, OrderResponseModel, \
    ToppingsResponseModel, ProductResponseModel
from backend.settings import JWT_SECRET_KEY, JWT_ALGORITHM
from bot.bot_funcs import send_order, send_login_code
from urls.dependencies import get_current_active_user, get_current_user

router = APIRouter()


def create_token(customer: Customer) -> str:
    user_data = {
        "sub": str(customer.phone_number),
        "exp": datetime.utcnow() + timedelta(days=14)
    }
    return jwt.encode(user_data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


@router.get('/products',
            tags=['common'],
            description='Возвращает список продуктов и его вариации',
            response_model=List[ProductResponseModel])
async def get_products():
    products = []
    for prod in Product.select():
        variations = [var.data(hide=['product']) for var in prod.variations]

        prod_with_vars = prod.data(hide=['img'])
        prod_with_vars.update({'variations': variations})
        products.append(prod_with_vars)
    return products


@router.get('/coffee_houses',
            tags=['common'],
            description='Возвращает список кофеен с именем и расположением',
            response_model=List[CoffeeHouseResponseModel])
async def get_coffeehouses():
    return [h.data(hide=('chat_id', 'is_open')) for h in CoffeeHouse.select()]


@router.get('/order_status/{number}',
            tags=['jwt require'],
            description='Возвращает статус заказа по его id или ошибку, если заказа нет',
            response_description='В ожидании | Принят | Отклонен | Выполнен | Не выполнен')
async def get_order_status(number: int, customer: Customer = Depends(get_current_user)):
    order = Order.get_or_none(number)
    if order is None:
        raise HTTPException(status_code=400, detail="Неверный номер заказа")
    if order.customer != customer:
        raise HTTPException(status_code=400, detail="Это заказ другого пользователя")
    return order.get_status_name()


@router.get('/products_various/{prod_id}',
            tags=['common'],
            description='Возвращает все вариации продукта или ошибку, если продукта нет',
            response_model=List[ProductsVariousResponseModel])
async def get_products_various(prod_id: int):
    if Product.get_or_none(prod_id) is None:
        raise HTTPException(status_code=400, detail='Invalid product id')

    prods = ProductVarious.select().where(ProductVarious.product == prod_id)
    return [p.data(hide=['product']) for p in prods]


@router.get('/toppings',
            tags=['common'],
            description='Возвращает список топингов',
            response_model=List[ToppingsResponseModel])
async def get_toppings():
    return [t.data() for t in Topping.select()]


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


@router.post('/make_order',
             tags=['jwt require'],
             description='Служит для создания заказа',
             response_model=OrderResponseModel)
async def make_order(order_inf: schemas.Order,
                     background_tasks: BackgroundTasks,
                     customer: Customer = Depends(get_current_active_user)):
    coffee_house: CoffeeHouse = CoffeeHouse.get(CoffeeHouse.id == order_inf.coffee_house)
    order = Order.create(coffee_house=coffee_house, customer=customer, time=order_inf.time)
    for p in order_inf.products:
        prod: ProductVarious = ProductVarious.get(ProductVarious.id == p.id)
        order_prod = OrderedProduct.create(order=order, product=prod)
        for top in p.toppings:
            ToppingToProduct.create(ordered_product=order_prod, topping=top)

    background_tasks.add_task(send_order, order.id)
    return {'order_number': order.id}


@router.post('/register_customer',
             description='Служит для создание аккаунта покупателя',
             response_description="Возвращает jwt-токен customer'а")
async def register_customer(customer: schemas.Customer):
    if Customer.get_or_none(phone_number=customer.phone_number):
        raise HTTPException(status_code=400, detail='Пользователь с таким номером телефона уже существует.')

    new_customer = Customer.create(name=customer.name, phone_number=customer.phone_number)
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
async def create_login_code(customer_data: schemas.Customer, background_tasks: BackgroundTasks):
    customer = Customer.get_or_none(phone_number=customer_data.phone_number)
    if customer is None:
        raise HTTPException(status_code=400, detail='Пользователя с таким номером телефона не существует.')
    if not customer.confirmed:
        raise HTTPException(status_code=401, detail='Пользователь не подтвердил номер телефона.')

    code = random.randint(100000, 999999)
    while LoginCode.get_or_none(code=code):
        code = random.randint(100000, 999999)

    login_code_data = {
        "customer": customer,
        "code": code,
        "expire": datetime.utcnow() + timedelta(minutes=5)
    }
    background_tasks.add_task(send_login_code, LoginCode.create(**login_code_data))
    return "Success"


@router.get('/verify_login_code',
            description='Для проверки login кода и получения jwt-токена',
            response_description='Возвращает jwt-токен')
async def verify_login_code(code: int):
    login_code: LoginCode = LoginCode.get_or_none(code=code)
    if login_code is None:
        raise HTTPException(status_code=401, detail='Неверный код подтверждения.')
    if login_code.expire < datetime.utcnow():
        raise HTTPException(status_code=401, detail='Срок действия кода подтверждения истек.')

    return create_token(login_code.customer)


@router.get('/my_orders',
            tags=['jwt require'],
            description="Возвращает историю заказов")
async def get_my_order_history(customer: Customer = Depends(get_current_user)):
    pass
