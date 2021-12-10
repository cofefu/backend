from backend import schemas
from app.models import User, Order, Product, Feedback

from fastapi import FastAPI
from fastapi import HTTPException, Response

from . import hasher

app = FastAPI(redoc_url=None, docs_url=None)


@app.post('/register')
async def register(user: models.User):
    if User.get_or_none(User.phone_number == user.phone_number) is not None:
        return HTTPException(400, 'This phone number is already registered')

    user.password = hasher.hash_psw(user.password)
    User.create(**dict(user))

    # TODO good response
    return Response('The phone number was successfully registered')


@app.post('/login')
async def login(user: models.User):
    usr: User = User.get_or_none(User.phone_number == user.phone_number)
    if usr is None or not hasher.validate(user.password, usr.password):
        return HTTPException(400, 'Invalid phone number or password')

    return Response('Success')


@app.get('/products')
async def get_products():
    return [p.data() for p in Product.select()]


@app.put('/make_order')  # REDO maybe post
async def make_order(order: models.Order):
    order = Order.create(**dict(order))
    return order


@app.post('/feedback')
async def feedback(fb: models.Feedback):
    user = User.get_or_none(User.id == fb.user)
    if user is None:
        return HTTPException(400, 'User not exist')
    Feedback.create(user=user.id, text=fb.text)
    return Response('Thank you for your feedback')
