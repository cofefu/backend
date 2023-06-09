from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_active_user, get_not_baned_user, timeout_is_over
from app.models import Customer, Order, ProductInOrder
from bot.bot_funcs import send_order
from fastapiProject.scheduler import scheduler
from fastapiProject.settings import settings
from orders.dependencies import valid_ordered_product, valid_order_info
from orders.schemas import OrderedProductCreate, OrderCreate
from orders.services import get_or_create_cart, gen_order_number, valid_equal_coffee_house

router = APIRouter(prefix='/api')


@router.post('/add_prod2cart',
             tags=['jwt require'],
             description='Для добавления продукта в корзину',
             status_code=status.HTTP_200_OK)
async def add_prod2cart(
        product_to_order: Annotated[OrderedProductCreate, Depends(valid_ordered_product)],
        customer: Annotated[Customer, Depends(get_current_active_user)],
        db: Annotated[Session, Depends(get_db)]):
    cart: Order = get_or_create_cart(customer, db)
    ordered_prod = ProductInOrder(
        order_id=cart.id,
        product_various_id=product_to_order.product_various_id,
        toppings=product_to_order.toppings
    )
    ordered_prod.save(db)


@router.post('/make_order_new',
             dependencies=[Depends(timeout_is_over)],
             tags=['jwt require'],
             description='Служит для создания заказа',
             status_code=status.HTTP_200_OK)
async def make_order_new(
        order_info: Annotated[OrderCreate, Depends(valid_order_info)],
        customer: Annotated[Customer, Depends(get_not_baned_user)],
        db: Annotated[Session, Depends(get_db)]):
    cart: Order = get_or_create_cart(customer, db)[0]
    if not valid_equal_coffee_house(cart.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Продукты принадлежат разным кофейням')
    elif not cart.products_in_order:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Корзина пуста')

    cart.coffee_house_branch_id = order_info.coffee_house_branch
    cart.comment = order_info.comment
    cart.time = order_info.time
    cart.order_number = gen_order_number()
    db.commit()

    scheduler.add_job(send_order,
                      'date',
                      timezone='utc',
                      run_date=datetime.utcnow() + settings.time_to_cancel_order,
                      replace_existing=True,
                      args=[cart.id],
                      id=str(cart.id))
    return {'order_number': cart.order_number}
