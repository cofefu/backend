from datetime import time, datetime

from pydantic import BaseModel


class CoffeeHouseBranchResponse(BaseModel):
    id: int
    placement: str
    open_time: time | None
    close_time: time | None


class CoffeeHouseResponse(BaseModel):
    coffee_house_name: str
    branches: list[CoffeeHouseBranchResponse]


class ProductsVariousResponseModel(BaseModel):
    id: int
    size_name: str  # ProductSize.name
    price: int


class ToppingsResponseModel(BaseModel):
    id: int
    name: str
    price: int


class ProductResponseModel(BaseModel):
    id: int
    name: str
    description: str | None
    tags: list[str]
    variations: list[ProductsVariousResponseModel]


class ProductsWithTypesResponse(BaseModel):
    type_name: str
    products: list[ProductResponseModel]


class SmallProductResponseModel(BaseModel):
    id: int
    toppings: list[int]


class CoffeeHouseMenuResponse(BaseModel):
    coffee_house_name: str
    time: datetime
    products: list[ProductsWithTypesResponse]
    toppings: list[ToppingsResponseModel]


class CoffeeHouseBranchWorktime(BaseModel):
    open_time: time | None
    close_time: time | None
