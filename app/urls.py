import random
from typing import List

from apscheduler.jobstores.base import JobLookupError
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Body
from pydantic import constr
from sqlalchemy.orm import Session
from starlette.responses import FileResponse
from jose import jwt
from datetime import datetime, timedelta
from pytz import timezone

from app.models import (ProductVarious, Product, Topping, CoffeeHouse, Customer,
                        Order, OrderedProduct, ToppingToProduct, LoginCode, Worktime, MenuUpdateTime)
from fastapiProject import schemas
from fastapiProject.scheduler import scheduler
from fastapiProject.settings import JWT_SECRET_KEY, JWT_ALGORITHM
from bot.bot_funcs import send_order, send_login_code, send_feedback_to_telegram, send_bugreport_to_telegram
from app.dependencies import get_current_active_user, get_current_user, get_not_baned_user, timeout_is_over, get_db

router = APIRouter(prefix='/api')


def create_token(customer: Customer) -> str:
    user_data = {
        "sub": str(customer.phone_number),
        "exp": datetime.utcnow() + timedelta(days=14)
    }
    return jwt.encode(user_data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


@router.get('/products',
            tags=['common'],
            description='Возвращает список продуктов и его вариации',
            response_model=List[schemas.ProductResponseModel])
async def get_products(db: Session = Depends(get_db)):
    products = []
    for product in db.query(Product).all():
        product_with_vars = product.data()
        product_var = [var.data() for var in product.variations]
        product_with_vars.update({'variations': product_var})
        products.append(product_with_vars)

    return products


@router.get('/coffee_houses',
            tags=['common'],
            description='Возвращает список кофеен с именем и расположением',
            response_model=List[schemas.CoffeeHouseResponseModel])  # redo
async def get_coffeehouses(db: Session = Depends(get_db)):
    response = []
    for house in db.query(CoffeeHouse).all():
        house_data = house.data('chat_id', 'is_open')

        weekday = datetime.now(tz=timezone('Asia/Vladivostok')).weekday()
        worktime = db.query(Worktime).filter(
            Worktime.coffee_house == house.id,
            Worktime.day_of_week == weekday
        ).one_or_none()

        if worktime is None or (not house.is_open):
            house_data.update({'open_time': None, 'close_time': None})
        else:
            house_data.update(worktime.data('id', 'day_of_week', 'coffee_house'))
        response.append(house_data)
    return response


@router.get('/order_status/{number}',
            tags=['jwt require'],
            description='Возвращает статус заказа по его id или ошибку, если заказа нет',
            response_description='В ожидании | Принят | Отклонен | Выполнен | Не выполнен')
async def get_order_status(number: int, customer: Customer = Depends(get_current_active_user),
                           db: Session = Depends(get_db)):
    order = db.query(Order).filter_by(id=number).one_or_none()
    if order is None:
        raise HTTPException(status_code=400, detail="Неверный номер заказа")
    if order.customer != customer:
        raise HTTPException(status_code=400, detail="Это заказ другого пользователя")
    return order.get_status_name()


# TEST delete
@router.get('/products_various/{prod_id}',
            tags=['common'],
            description='Возвращает все вариации продукта или ошибку, если продукта нет',
            response_model=List[schemas.ProductsVariousResponseModel]
            )
async def get_products_various(prod_id: int, db: Session = Depends(get_db)):
    product: Product = db.query(Product).filter_by(id=prod_id).one_or_none()
    if product is None:
        raise HTTPException(status_code=400, detail='Несуществующий идентификатор продукта')
    return [variation.data() for variation in product.variations]


@router.get('/toppings',
            tags=['common'],
            description='Возвращает список топингов',
            response_model=List[schemas.ToppingsResponseModel])
async def get_toppings(db: Session = Depends(get_db)):
    return [t.data() for t in db.query(Topping).all()]


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


# REDO make_order
@router.post('/make_order',
             dependencies=[Depends(timeout_is_over)],
             tags=['jwt require'],
             description='Служит для создания заказа',
             response_model=schemas.OrderNumberResponseModel)
async def make_order(order_inf: schemas.OrderIn,
                     customer: Customer = Depends(get_not_baned_user),
                     db: Session = Depends(get_db)):
    coffee_house: CoffeeHouse = db.query(CoffeeHouse).filter_by(id=order_inf.coffee_house).one()
    order = Order(coffee_house_id=coffee_house.id,
                  customer_id=customer.id,
                  time=order_inf.time,
                  comment=order_inf.comment)
    db.add(order)
    db.commit()
    for p in order_inf.products:
        prod: ProductVarious = db.query(ProductVarious).filter_by(id=p.id).one()
        order_prod = OrderedProduct(order=order, product=prod)
        for top in p.toppings:
            topping = ToppingToProduct(ordered_product=order_prod, topping=top)

    scheduler.add_job(send_order,
                      'date',
                      timezone='utc',
                      run_date=datetime.utcnow() + timedelta(minutes=1),
                      replace_existing=True,
                      args=[order.id],
                      id=str(order.id))
    return {'order_number': order.id}


# TEST cancel_order
@router.put('/cancel_order',
            tags=['jwt require'],
            description='Служит для отмены заказа')
async def cancel_order(order_number: int,
                       customer: Customer = Depends(get_current_active_user),
                       db: Session = Depends(get_db)):
    if db.query(Order).filter_by(id=order_number, customer_id=customer.id).delete() == 0:
        raise HTTPException(status_code=400, detail='Заказ не найден.')
    try:
        scheduler.remove_job(str(order_number))
        db.commit()
        return 'Ok'
    except JobLookupError:
        raise HTTPException(status_code=400, detail='Отменить заказ уже нельзя.')


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
async def create_login_code(customer_data: schemas.Customer,
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


@router.get('/my_orders',
            tags=['jwt require'],
            description="Возвращает историю заказов",
            response_model=List[schemas.OrderResponseModel])
async def get_my_order_history(customer: Customer = Depends(get_current_active_user),
                               db: Session = Depends(get_db)):
    orders = []
    for order in db.query(Order).filter_by(customer_id=customer).all():
        orders.append(schemas.OrderResponseModel.to_dict(order))
    return orders


@router.get('/me',
            tags=['jwt require'],
            description='Возвращает информацию о текущем пользователе',
            response_model=schemas.Customer)
async def get_me(customer: Customer = Depends(get_current_user)):
    return customer.data()


@router.get('/last_order',
            tags=['jwt require'],
            description='Возвращает последний заказ пользователя',
            response_model=schemas.OrderResponseModel)
async def get_last_order(customer: Customer = Depends(get_current_active_user),
                         db: Session = Depends(get_db)):
    order = db.query(Order).filter_by(customer_id=customer.id).join(Customer).order_by(Order.id.desc()).first()
    if len(order) == 0:
        return None
    return schemas.OrderResponseModel.to_dict(order[0])


@router.get('/active_orders',
            tags=['jwt require'],
            description='Возвращает активные заказы пользователя',
            response_model=List[schemas.OrderResponseModel])
async def get_active_orders(customer: Customer = Depends(get_current_active_user),
                            db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.customer_id == customer.id, Order.status.in_([0, 1, 5])).order_by(
        Order.id.desc()).all()
    return [schemas.OrderResponseModel.to_dict(order) for order in orders]


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
    return customer  # TEST without .data()


@router.get('/is_confirmed',
            tags=['jwt require'],
            description='Узнать подтвержден ли номер телефона')
async def get_user_is_confirmed(customer: Customer = Depends(get_current_user)):
    return bool(customer.confirmed)


@router.get('/menu',
            tags=['common'],
            description='Сверить последнюю дату обновления БД',
            response_model=schemas.MenuResponseModel)
async def check_menu_update(time: datetime = None,
                            db: Session = Depends(get_db)):
    menu_update = db.query(MenuUpdateTime).one_or_none()
    if menu_update.time == time:
        return None
    return {
        "time": menu_update.time,
        "products": await get_products(),
        "toppings": await get_toppings()
    }
