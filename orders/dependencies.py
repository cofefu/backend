from datetime import datetime, timedelta
from typing import Annotated
from pytz import timezone

from fastapi import Depends, HTTPException, Body, status
from pydantic import constr
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import CoffeeHouseBranch, Worktime, DaysOfWeek, Customer, Order
from auth.dependencies import get_current_active_user
from fastapiProject.settings import settings
from menu.dependencies import valid_coffee_house_branch_id, valid_product_various_id, valid_topping_id
from orders.schemas import OrderCreate, ProductInCartCreate
from orders.services import min_order_preparation_time


async def valid_order_time(
        time: Annotated[datetime, Body()],
        coffee_house_branch: Annotated[CoffeeHouseBranch, Depends(valid_coffee_house_branch_id)],
        db: Annotated[Session, Depends(get_db)],
) -> datetime:
    """
    Check that the coffee shop branch is open and the order will have time to prepare.
    :param time: time of order issue
    :param coffee_house_branch: coffee shop for ordering
    :param db: sqlalchemy session
    :return: valid time
    """
    time = timezone('Asia/Vladivostok').localize(time)
    now = datetime.now(tz=timezone('Asia/Vladivostok'))
    min_time = min_order_preparation_time(time)
    max_time = timedelta(hours=5)
    if not (min_time - timedelta(seconds=10) <= time - now <= max_time):
        raise HTTPException(status_code=400,
                            detail=f"Неправильное время заказа. Минимальное время приготовления заказа - "
                                   f"{min_time.seconds // 60} минут")

    weekday = datetime.now(tz=timezone('Asia/Vladivostok')).weekday()
    worktime: Worktime = (db.query(Worktime)
                          .filter_by(coffee_house_branch_id=coffee_house_branch.id,
                                     day_of_week=DaysOfWeek(weekday))
                          .first())
    if worktime is None or (not coffee_house_branch.is_active):
        raise HTTPException(status_code=400, detail="Кофейня закрыта")

    open_time = worktime.open_time
    close_time = worktime.close_time
    if not open_time <= time.time() <= close_time:
        raise HTTPException(status_code=400, detail="Кофейня закрыта")

    return time


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
        coffee_house_branch_id=coffee_house_branch.id,
        comment=comment,
        time=time
    )


def valid_timeout_between_orders(
        customer: Annotated[Customer, Depends(get_current_active_user)],
        db: Annotated[Session, Depends(get_db)]
) -> None:
    last_order: Order = (db.query(Order)
                         .filter_by(customer_phone_number=customer.phone_number)
                         .join(Customer)
                         .order_by(Order.id.desc())
                         .first())
    if last_order is None:
        return

    if datetime.utcnow() - last_order.creation_time <= settings.order_timeout:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                            detail=f'С момента последнего заказа прошло менее 2 минут')
