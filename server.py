from fastapi import FastAPI, HTTPException
from starlette.responses import FileResponse

from app.models import *
from backend import schemas

app = FastAPI(redoc_url=None, docs_url=None)


@app.get('/products')
async def get_products():
    return [p.data(hide=['description']) for p in Product.select()]


# TEST return svg or ico depending on the user's browser
@app.get('/favicon.svg')
async def get_favicon_svg():
    return FileResponse('assets/beans.svg')


@app.get('/favicon.ico')
async def get_favicon_svg():
    return FileResponse('assets/beans.ico')


@app.post('/make_order')
async def make_order(order: schemas.Order):
    customer: Customer = Customer.get_or_create(**dict(order.customer))[0]
    coffee_house: CoffeeHouse = CoffeeHouse.get_or_none(CoffeeHouse.name == order.coffee_house)
    product: Product = Product.get_or_none(Product.id == order.product)

    if coffee_house is None:
        return HTTPException(400, 'Incorrect coffee house')
    if product is None:
        return HTTPException(400, 'Incorrect product')

    order = Order.create(coffee_house=coffee_house, customer=customer, product=product, time=order.time)
    return 'Success'
