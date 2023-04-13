from datetime import datetime, timedelta, time
from typing import List, Optional

from fastapi import HTTPException
from pydantic import BaseModel, validator, constr
from pytz import timezone
from sqlalchemy.orm import Session

from app import models
from app.models import CoffeeHouse, ProductVarious, Topping, Worktime, DaysOfWeek, ProductSizes, ProductTypes
from db import SessionLocal
from fastapiProject.settings import settings

time_breaks = (
    datetime(year=datetime.now().year, month=1, day=1, hour=10),
    datetime(year=datetime.now().year, month=1, day=1, hour=11, minute=40),
    datetime(year=datetime.now().year, month=1, day=1, hour=13, minute=20),
    datetime(year=datetime.now().year, month=1, day=1, hour=15),
    datetime(year=datetime.now().year, month=1, day=1, hour=16, minute=40)
)


def min_order_preparation_time(order_time: datetime) -> timedelta:
    shift = timedelta(minutes=5)
    for time_break in time_breaks:
        if (time_break - shift).time() < order_time.time() < (time_break + timedelta(minutes=10) + shift).time():
            return timedelta(minutes=10)
    return timedelta(minutes=7)


class Customer(BaseModel):
    name: constr(max_length=20, strip_whitespace=True)
    phone_number: constr(min_length=10, max_length=10, strip_whitespace=True)

    class Config:
        schema_extra = {
            "example": {
                "name": "Иван",
                "phone_number": "9997773322"
            }
        }

    @validator('phone_number')
    def phone_number_validator(cls, number: str):
        try:
            int(number)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Номер телефона не является числом")
        return number


class Product(BaseModel):
    id: int
    toppings: List[int]

    @validator('id')
    def product_validator(cls, prod: int):
        db: Session
        with SessionLocal() as db:
            if db.get(ProductVarious, prod) is None:
                raise HTTPException(status_code=400, detail=f"Несуществующий идентификатор продукта: {prod}")
            return prod

    @validator('toppings')
    def toppings_validator(cls, toppings: List[int]):
        db: Session
        with SessionLocal() as db:
            for top_id in toppings:
                if db.get(Topping, top_id) is None:
                    raise HTTPException(status_code=400, detail=f'Несуществующий идентификатор топинга: {top_id}')
            return toppings


class OrderIn(BaseModel):
    coffee_house: str  # TEST maybe int
    comment: constr(max_length=200, strip_whitespace=True) = None
    products: List[Product]
    time: datetime

    class Config:
        schema_extra = {
            "example": {
                "coffee_house": "1",
                "products": [
                    {
                        "id": 1,
                        "toppings": []
                    },
                    {
                        "id": 3,
                        "toppings": [2]
                    }
                ],
                "comment": "Хочу много сахара и воду без газа",
                "time": (datetime.now() + timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M"),
            }
        }

    @validator('coffee_house')
    def coffeehouse_validator(cls, coffee_house: str):
        db: Session
        with SessionLocal() as db:
            if db.get(CoffeeHouse, coffee_house) is None:
                raise HTTPException(status_code=400, detail=f"Несуществующий идентификатор кофейни: {coffee_house}")
            return coffee_house

    @validator('time')
    def time_validator(cls, order_time: datetime, values: dict):
        if values.get('coffee_house') is None:
            return order_time
        db: Session
        with SessionLocal() as db:
            house: CoffeeHouse = db.get(CoffeeHouse, values.get('coffee_house'))

            order_time = timezone('Asia/Vladivostok').localize(order_time)
            now = datetime.now(tz=timezone('Asia/Vladivostok'))
            min_time = min_order_preparation_time(order_time)
            max_time = timedelta(hours=5)
            if not (min_time - timedelta(seconds=10) <= order_time - now <= max_time):
                raise HTTPException(status_code=400,
                                    detail=f"Неправильное время заказа. Минимальное время приготовления заказа - "
                                           f"{min_time.seconds // 60} минут")

            weekday = datetime.now(tz=timezone('Asia/Vladivostok')).weekday()
            worktime: Worktime = (db.query(Worktime)
                                  .filter_by(coffee_house_id=house.id, day_of_week=DaysOfWeek(weekday))
                                  .first())
            if worktime is None or (not house.is_open):
                raise HTTPException(status_code=400, detail="Кофейня закрыта")

            open_time = worktime.open_time
            close_time = worktime.close_time
            if not open_time <= order_time.time() <= close_time:
                raise HTTPException(status_code=400, detail="Кофейня закрыта")

            return order_time

    @validator('products')
    def products_validator(cls, products: list):
        if len(products) > settings.max_product_in_order:
            raise HTTPException(status_code=400,
                                detail=f"Нельзя заказать более {settings.max_product_in_order} продуктов из меню.")
        return products


class CoffeeHouseResponseModel(BaseModel):
    id: int
    name: str
    placement: str
    open_time: Optional[time]
    close_time: Optional[time]


class ProductsVariousResponseModel(BaseModel):
    id: int
    size: ProductSizes
    price: int


class OrderNumberResponseModel(BaseModel):
    order_number: int


class ToppingsResponseModel(BaseModel):
    id: int
    name: str
    price: int


class ProductResponseModel(BaseModel):
    id: int
    type: ProductTypes
    name: str
    description: str | None
    variations: List[ProductsVariousResponseModel]


class SmallProductResponseModel(BaseModel):
    id: int
    toppings: List[int]


class OrderResponseModel(BaseModel):
    order_number: int
    coffee_house: int
    comment: str = None
    time: datetime
    status: str
    products: List[SmallProductResponseModel]

    @staticmethod
    def to_dict(order: models.Order) -> dict:
        products = []
        for prod in order.ordered_products:
            toppings = []
            for top in prod.toppings:
                toppings.append(top.topping.id)
            products.append({"id": prod.product_various.id, "toppings": toppings})
        data = {
            "order_number": order.id,
            "coffee_house": order.coffee_house.id,
            "comment": order.comment,
            "time": order.time,
            "status": order.get_status_name(),
            "products": products
        }
        return data

    class Config:
        schema_extra = {
            "example": {
                "order_number": 4,
                "coffee_house": 1,
                "time": "2022-04-12 19:59",
                "status": "Принят",
                "comment": "Хочу много сахара и воду без газа",
                "products": [
                    {
                        "id": 26,
                        "toppings": [11]
                    },
                    {
                        "id": 25,
                        "toppings": [3]
                    }
                ]
            }
        }


class MenuResponseModel(BaseModel):
    time: datetime
    products: List[ProductResponseModel]
    toppings: List[ToppingsResponseModel]
