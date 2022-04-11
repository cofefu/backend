from typing import List

from fastapi import APIRouter, HTTPException
from starlette.responses import FileResponse
from peewee import fn, JOIN

from app.models import ProductVarious, Product, Topping, CoffeeHouse, Customer, Order, OrderedProduct, \
    ToppingToProduct
from backend import schemas
from backend.schemas import CoffeeHouseResponseModel, ProductsVariousResponseModel, OrderResponseModel, \
    ToppingsResponseModel, ProductResponseModel
from bot.bot_funcs import send_order

router = APIRouter()


@router.get('/products',
            tags=['common'],
            description='Возвращает список продуктов и его вариации',
            response_model=List[ProductResponseModel])
async def get_products():
    products = []
    for prod in Product.select():
        variations = [var.data(hide=['product']) for var in prod.variations]

        prod_with_vars = prod.data(hide=['img'])
        prod_with_vars['variations'] = variations
        products.append(prod_with_vars)
    return products


@router.get('/coffee_houses',
            tags=['common'],
            description='Возвращает список кофеен с именем и расположением',
            response_model=List[CoffeeHouseResponseModel])
async def get_coffeehouses():
    return [h.data(hide=('chat_id', 'is_open')) for h in CoffeeHouse.select()]


@router.get('/order_status/{number}',
            description='Возвращает статус заказа по его id или ошибку, если заказа нет')
async def get_order_status(number: int):
    order = Order.get_or_none(number)
    if order is None:
        raise HTTPException(status_code=400, detail="Invalid order number")
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
             description='Служит для создания заказа',
             response_model=OrderResponseModel)
async def make_order(order_inf: schemas.Order):
    coffee_house: CoffeeHouse = CoffeeHouse.get(CoffeeHouse.id == order_inf.coffee_house)
    customer: Customer = Customer.get_or_create(**dict(order_inf.customer))[0]  # redo
    order = Order.create(coffee_house=coffee_house, customer=customer, time=order_inf.time)
    for p in order_inf.products:
        prod: ProductVarious = ProductVarious.get(ProductVarious.id == p.id)
        order_prod = OrderedProduct.create(order=order, product=prod)
        for top in p.toppings:
            ToppingToProduct.create(ordered_product=order_prod, topping=top)

    send_order(order_number=order.id)
    return {'order_number': order.id}


@router.post('/make_customer',
             description='Служит для создание аккаунта покупателя')
async def make_customer(customer: schemas.Customer):
    Customer.create(name=customer.name, phone_number=customer.phone_number)

    return "Success"  # todo возвращать jwt token
