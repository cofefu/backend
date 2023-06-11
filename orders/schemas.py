from datetime import datetime, timedelta

from pydantic import BaseModel, validator, constr

from app.models import Order
from fastapiProject.schemas import SmallProductResponseModel


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


class OrderResponse(BaseModel):
    order_id: int
    order_number: str
    coffee_house_branch_id: int
    comment: str = None
    time: datetime
    status: str
    products: list[SmallProductResponseModel]

    @staticmethod
    def to_dict(order: Order) -> dict:
        products = []
        for prod in order.products_in_order:
            toppings = []
            for top in prod.toppings:
                toppings.append(top.topping.id)
            products.append({"id": prod.product_various.id, "toppings": toppings})
        data = {
            "order_id": order.id,
            "order_number": order.order_number,
            "coffee_house_branch_id": order.coffee_house_branch_id,
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
