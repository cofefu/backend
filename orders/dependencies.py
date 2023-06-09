from datetime import datetime
from typing import Annotated

from fastapi import Depends, HTTPException, status, Body
from pydantic import constr
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_not_baned_user
from app.models import CoffeeHouseBranch, Customer, ProductVarious, Topping
from orders.schemas import OrderCreate, ProductInCartCreate


async def valid_coffee_house_branch_id(
        coffee_house_branch_id: Annotated[int, Body()],
        sess: Annotated[Session, Depends(get_db)]
) -> CoffeeHouseBranch:
    branch = sess.query(CoffeeHouseBranch).get(coffee_house_branch_id)
    if branch is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Неверный идентификатор кофейни')
    return branch


# todo implement this
async def valid_order_time(
        time: Annotated[datetime, Body()],
        db: Annotated[Session, Depends(get_db)],
) -> datetime:
    return time


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


async def valid_ordered_product(
        id: Annotated[int, Depends(valid_product_various_id)],
        toppings: Annotated[
            list[Annotated[int, Depends(valid_topping_id)]],
            Body(embed=True)
        ]
) -> ProductInCartCreate:
    return ProductInCartCreate(
        product_various_id=id,
        toppings=toppings
    )


async def valid_order_info(
        coffee_house_branch: Annotated[CoffeeHouseBranch, Depends(valid_coffee_house_branch_id)],
        time: Annotated[datetime, Depends(valid_order_time)],
        comment: Annotated[constr(max_length=200, strip_whitespace=True) | None, Body(embed=True)] = None,
) -> OrderCreate:
    """
    Проверяет информацию, переданную для создания заказа (кофейню, комментарий, время).
    Возвращает проверенный pydantic класс заказа.
    :rtype: OrderCreate
    """
    return OrderCreate(
        coffee_house_branch=coffee_house_branch.id,
        comment=comment,
        time=time
    )
