from datetime import datetime, timedelta

from pydantic import BaseModel, validator, constr


class ProductInCartCreate(BaseModel):
    product_various_id: int
    toppings: list[int]


class OrderCreate(BaseModel):
    coffee_house_branch_id: int
    comment: constr(max_length=200, strip_whitespace=True) = None
    time: datetime

    class Config:
        schema_extra = {
            "example": {
                "coffee_house_branch_id": "1",
                "comment": "Хочу много сахара и воду без газа",
                "time": (datetime.now() + timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M"),
            }
        }
