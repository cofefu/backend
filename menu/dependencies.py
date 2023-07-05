from typing import Annotated

from fastapi import Body, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from db.dependencies import get_db
from app.models import CoffeeHouseBranch, ProductVarious, Topping, CoffeeHouse


async def valid_coffee_house_branch_id(
        coffee_house_branch_id: Annotated[int, Body()],
        sess: Annotated[Session, Depends(get_db)]
) -> CoffeeHouseBranch:
    branch = sess.query(CoffeeHouseBranch).get(coffee_house_branch_id)
    if branch is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Неверный идентификатор филиала кофейни')
    return branch


async def valid_coffee_house_name(
        coffee_house_name: Annotated[str, Query],
        sess: Annotated[Session, Depends(get_db)]
) -> CoffeeHouse:
    coffee_house = sess.query(CoffeeHouse).get(coffee_house_name)
    if coffee_house is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Неверный идентификатор кофейни')
    return coffee_house


async def valid_product_various_id(
        prod_var_id: Annotated[int, Body()],
        sess: Annotated[Session, Depends(get_db)]
) -> int:
    prod_var = sess.query(ProductVarious).get(prod_var_id)
    if prod_var is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Неверный идентификатор вариации продукта')
    return prod_var_id


async def valid_topping_id(
        topping_id: Annotated[int, Body()],
        sess: Annotated[Session, Depends(get_db)]
) -> int:
    topping = sess.query(Topping).get(topping_id)
    if topping is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Неверный идентификатор топинга')
    return topping_id
