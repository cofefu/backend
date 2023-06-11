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


class MenuResponseModel(BaseModel):
    time: datetime
    products: List[ProductResponseModel]
    toppings: List[ToppingsResponseModel]
