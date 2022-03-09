from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException
from starlette.responses import FileResponse
import telebot
from pytz import timezone

from app.models import *
from backend import schemas
from backend.settings import API_TOKEN, WEBHOOK_SSL_CERT, DOMAIN, SERVER_PORT
from bot import bot
from bot.bot_funcs import send_order
from bot.email_sender import send_email

app = FastAPI(redoc_url=None, docs_url=None)


@app.on_event("startup")
async def on_startup():
    pass
    # bot.remove_webhook()
    # bot.set_webhook(url=f"https://{DOMAIN}:{SERVER_PORT}" + f'/{API_TOKEN}/',
    #                 certificate=open(WEBHOOK_SSL_CERT, 'r'))


@app.get('/products')
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


@app.get('/products_various/{prod_id}')
async def get_products_various(prod_id: int):
    prods = ProductVarious.select().where(ProductVarious.product == prod_id)
    return [p.data(hide=['product']) for p in prods]


@app.get('/toppings')
async def get_toppings():
    return [t.data() for t in Topping.select()]


# TEST return svg or ico depending on the user's browser
@app.get('/favicon.svg')
async def get_favicon_svg():
    return FileResponse('assets/beans.svg')


@app.get('/favicon.ico')
async def get_favicon_svg():
    return FileResponse('assets/beans.ico')


def validate_toppings(toppings: List[int]) -> bool:
    for top in toppings:
        if Topping.get_or_none(Topping.id == top) is None:
            return False
    return True


def validate_products(products: List[schemas.Product]) -> bool:
    for prod in products:
        p = ProductVarious.get_or_none(ProductVarious.id == prod.id)
        if p is None or not validate_toppings(prod.toppings):
            return False
    return True


def validate_coffeehouse(coffee_house: str) -> bool:
    if CoffeeHouse.get_or_none(coffee_house) is None:
        return False
    return True


def validate_worktime(time: datetime, coffee_house: str) -> bool:
    weekday = datetime.now(tz=timezone('Asia/Vladivostok')).weekday()
    for timetbl in TimeTable.select().where(TimeTable.coffee_house == coffee_house):
        if timetbl.worktime.day_of_week == weekday:
            open_time = datetime.strptime(timetbl.worktime.open_time, '%H:%M:%S').time()
            close_time = datetime.strptime(timetbl.worktime.close_time, '%H:%M:%S').time()
            if open_time <= time.time() <= close_time:
                return True
            return False
    return False


@app.post('/make_order')
async def make_order(order_inf: schemas.Order):
    if not validate_coffeehouse(order_inf.coffee_house):
        return HTTPException(400, 'Incorrect coffee house')
    if not validate_products(order_inf.products):
        return HTTPException(400, 'Incorrect product id')
    if not validate_worktime(order_inf.time, order_inf.coffee_house):
        return HTTPException(400, 'Incorrect worktime')

    coffee_house: CoffeeHouse = CoffeeHouse.get(order_inf.coffee_house)
    customer: Customer = Customer.get_or_create(**dict(order_inf.customer))[0]
    order = Order.create(coffee_house=coffee_house, customer=customer, time=order_inf.time)
    for p in order_inf.products:
        prod: ProductVarious = ProductVarious.get(ProductVarious.id == p.id)
        order_prod = OrderedProduct.create(order=order, product=prod)
        for top in p.toppings:
            ToppingToProduct.create(ordered_product=order_prod, topping=top)

    send_order(order_number=order.id)
    return 'Success'


@app.post(f'/{API_TOKEN}/')
def process_webhook(update: dict):
    if update:
        update = telebot.types.Update.de_json(update)
        bot.process_new_updates([update])
    else:
        return


@bot.message_handler(commands=['start'])
def send_welcome(message):
    print(message.chat.id)
    bot.reply_to(message, f"Hello, i'm coffefu webhook bot. Chat {message.chat.id}")


@bot.callback_query_handler(func=lambda call: True)
def callback_processing(call):
    cb_ans, order_number = call.data.split()
    ans = 'Заказ принят' if cb_ans == 'yes' else 'Заказ отклонен'
    bot.answer_callback_query(call.id, ans)
    ans = f"\n<b>{ans}</b>"

    order = Order.get_or_none(id=int(order_number))
    status = (cb_ans == 'yes')
    order.status = status
    customer_email = order.customer.email

    send_email(customer_email, int(order_number), status)

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=call.message.text + ans, reply_markup=None)
