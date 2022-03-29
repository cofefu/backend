from fastapi import APIRouter, HTTPException
from starlette.responses import FileResponse
from peewee import fn

from app.models import ProductVarious, Product, Topping, CoffeeHouse, Customer, Order, OrderedProduct, \
    ToppingToProduct
from backend import schemas
from bot.bot_funcs import send_order

router = APIRouter()


@router.get('/products')
async def get_products():
    def unpack(p):
        p_tt = [tuple(p.items())[0]]
        p_new = tuple(p.values())[1]
        p_new.update(p_tt)
        return p_new

    products = (ProductVarious
                .select(Product.id, Product.name, Product.description, fn.min(ProductVarious.price))
                .join(Product)
                .group_by(Product.id)
                )
    return [unpack(p.data()) for p in products]


@router.get('/coffee_houses')
async def get_coffeehouses():
    return [h.data(hide=('chat_id', 'is_open')) for h in CoffeeHouse.select()]


@router.get('/order_status/{number}')
async def get_order_status(number: int):
    order = Order.get_or_none(number)
    if order is None:
        raise HTTPException(status_code=400, detail="Invalid order number")
    return order.status == 1


@router.get('/products_various/{prod_id}')
async def get_products_various(prod_id: int):
    prods = ProductVarious.select().where(ProductVarious.product == prod_id)
    return [p.data(hide=['product']) for p in prods]


@router.get('/toppings')
async def get_toppings():
    return [t.data() for t in Topping.select()]


# TEST return svg or ico depending on the user's browser
@router.get('/favicon.svg')
async def get_favicon_svg():
    return FileResponse('assets/beans.svg')


@router.get('/favicon.ico')
async def get_favicon_svg():
    return FileResponse('assets/beans.ico')


@router.post('/make_order')
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
