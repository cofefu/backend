from fastapi import HTTPException
from pydantic import BaseModel, constr, validator


class CustomerCreate(BaseModel):
    name: constr(max_length=20, strip_whitespace=True)  # todo change to special validator
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


class CustomerResponse(BaseModel):
    name: str
    phone_number: int


class CustomerNewName(BaseModel):
    new_name: constr(strip_whitespace=True)

    @validator('new_name')
    def new_name_validator(cls, new_name: str):
        if len(new_name) > 20:
            raise HTTPException(status_code=422, detail='Длина имени не может превышать 20 символов')
        return new_name