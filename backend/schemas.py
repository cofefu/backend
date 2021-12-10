import json
from datetime import datetime, timedelta
from pytz import timezone  # TODO try to delete
from pydantic import BaseModel, validator, constr
from pydantic.typing import List


class User(BaseModel):
    name: constr(max_length=20) = None
    phone_number: constr(max_length=20)
    password: constr(max_length=20)


# REDO Order pydantic model
class Order(BaseModel):
    coffee_house_name: str
    customer: int
    product: List[int]
    time: datetime

    @validator('time')
    def time_validator(cls, future: datetime):
        future = timezone('Asia/Vladivostok').localize(future)

        now = datetime.now(tz=timezone('Asia/Vladivostok'))
        min_time = timedelta(minutes=5)
        max_time = timedelta(hours=5)

        assert now < future and min_time <= future - now <= max_time, \
            "Incorrect order time. The allowed time is from 5 minutes to 5 hours"

        return future


class Feedback(BaseModel):
    user: int  # TEST id or phone_number
    text: constr(max_length=250)
