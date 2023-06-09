from datetime import datetime, timedelta, time
from typing import List, Optional

from fastapi import HTTPException
from pydantic import BaseModel, validator, constr
from pytz import timezone
from sqlalchemy.orm import Session

from app import models
from app.models import CoffeeHouse, ProductVarious, Topping, Worktime, DaysOfWeek, ProductSize, ProductType
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


class CoffeeHouseResponseModel(BaseModel):
    id: int
    name: str
    placement: str
    open_time: Optional[time]
    close_time: Optional[time]


class ProductsVariousResponseModel(BaseModel):
    id: int
    size: str  # ProductSize.name
    price: int


class OrderNumberResponseModel(BaseModel):
    order_number: int


class ToppingsResponseModel(BaseModel):
    id: int
    name: str
    price: int


class ProductResponseModel(BaseModel):
    id: int
    type: str  # ProductType
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
        for prod in order.products_in_order:
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
