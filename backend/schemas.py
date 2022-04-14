from datetime import datetime, timedelta
from typing import List

from fastapi import HTTPException
from pydantic import BaseModel, validator, constr, EmailStr
from pytz import timezone

from app import models
from app.models import CoffeeHouse, TimeTable, ProductVarious, Topping


class Customer(BaseModel):
    name: constr(max_length=20)
    phone_number: constr(max_length=10)

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
            raise HTTPException(status_code=400, detail=f"PhoneNumber not a number")
        return number


class Product(BaseModel):
    id: int
    toppings: List[int]

    @validator('id')
    def product_validator(cls, prod: int):
        if ProductVarious.get_or_none(ProductVarious.id == prod) is None:
            raise HTTPException(status_code=400, detail=f"Incorrect product id: {prod}")
        return prod

    @validator('toppings')
    def toppings_validator(cls, toppings: List[int]):
        for top in toppings:
            if Topping.get_or_none(Topping.id == top) is None:
                raise HTTPException(status_code=400, detail=f'Incorrect topping id: {top}')
        return toppings


class OrderIn(BaseModel):
    coffee_house: str  # TEST maybe int
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
                "time": "2022-03-29 22:59"
            }
        }

    @validator('coffee_house')
    def coffeehouse_validator(cls, coffee_house: str):
        if CoffeeHouse.get_or_none(coffee_house) is None:
            raise HTTPException(status_code=400, detail="Incorrect coffee_house id")
        return coffee_house

    @validator('time')
    def time_validator(cls, order_time: datetime, values: dict):
        order_time = timezone('Asia/Vladivostok').localize(order_time)

        now = datetime.now(tz=timezone('Asia/Vladivostok'))
        min_time = timedelta(minutes=5)
        max_time = timedelta(hours=5)
        if not (now < order_time and min_time <= order_time - now <= max_time):
            raise HTTPException(status_code=400,
                                detail="Incorrect order time. The allowed time is from 5 minutes to 5 hours")

        weekday = datetime.now(tz=timezone('Asia/Vladivostok')).weekday()
        for timetbl in TimeTable.select().where(TimeTable.coffee_house == values['coffee_house']):
            if timetbl.worktime.day_of_week == weekday:
                open_time = datetime.strptime(timetbl.worktime.open_time, '%H:%M:%S').time()
                close_time = datetime.strptime(timetbl.worktime.close_time, '%H:%M:%S').time()
                if not open_time <= order_time.time() <= close_time:
                    raise HTTPException(status_code=400, detail="The coffee house is closed")
        return order_time


class CoffeeHouseResponseModel(BaseModel):
    id: int
    name: str
    placement: str
    open_time: str
    close_time: str


class ProductsVariousResponseModel(BaseModel):
    id: int
    size: int
    price: int


class OrderNumberResponseModel(BaseModel):
    order_number: int


class ToppingsResponseModel(BaseModel):
    id: int
    name: str
    price: int


class ProductResponseModel(BaseModel):
    id: int
    type: int
    name: str
    description: str
    variations: List[ProductsVariousResponseModel]


class SmallProductResponseModel(BaseModel):
    id: int
    toppings: List[int]


class OrderResponseModel(BaseModel):
    order_number: int
    coffee_house: int
    time: str
    status: str
    products: List[SmallProductResponseModel]

    @staticmethod
    def to_dict(order: models.Order) -> dict:
        products = []
        for prod in order.ordered_products:
            toppings = []
            for top in prod.toppings:
                toppings.append(top.topping.id)
            products.append({"id": prod.product.id, "toppings": toppings})
        data = {
            "order_number": order.id,
            "coffee_house": order.coffee_house.id,
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
