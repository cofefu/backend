from datetime import datetime, timedelta

from pydantic import BaseModel, validator, constr


class OrderedProductCreate(BaseModel):
    product_various_id: int
    toppings: list[int]


class OrderCreate(BaseModel):
    coffee_house_branch: int
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

    # @validator('time')
    # def time_validator(cls, order_time: datetime, values: dict):
    #     if values.get('coffee_house') is None:
    #         return order_time
    #     db: Session
    #     with SessionLocal() as db:
    #         house: CoffeeHouse = db.get(CoffeeHouse, values.get('coffee_house'))
    #
    #         order_time = timezone('Asia/Vladivostok').localize(order_time)
    #         now = datetime.now(tz=timezone('Asia/Vladivostok'))
    #         min_time = min_order_preparation_time(order_time)
    #         max_time = timedelta(hours=5)
    #         if not (min_time - timedelta(seconds=10) <= order_time - now <= max_time):
    #             raise HTTPException(status_code=400,
    #                                 detail=f"Неправильное время заказа. Минимальное время приготовления заказа - "
    #                                        f"{min_time.seconds // 60} минут")
    #
    #         weekday = datetime.now(tz=timezone('Asia/Vladivostok')).weekday()
    #         worktime: Worktime = (db.query(Worktime)
    #                               .filter_by(coffee_house_id=house.id, day_of_week=DaysOfWeek(weekday))
    #                               .first())
    #         if worktime is None or (not house.is_open):
    #             raise HTTPException(status_code=400, detail="Кофейня закрыта")
    #
    #         open_time = worktime.open_time
    #         close_time = worktime.close_time
    #         if not open_time <= order_time.time() <= close_time:
    #             raise HTTPException(status_code=400, detail="Кофейня закрыта")
    #
    #         return order_time
