from datetime import datetime
from typing import Annotated

from apscheduler.jobstores.base import JobLookupError
from fastapi import APIRouter, Depends, status, HTTPException, Path, Body
from sqlalchemy.orm import Session

from src.db.dependencies import get_db
from src.auth.dependencies import get_current_active_user, get_not_baned_user
from src.orders.dependencies import valid_timeout_between_orders
from src.db.models import Customer, Order, ProductInCart, Topping2ProductInCart, OrderStatuses
from src.bot.services import send_order
from src.config.scheduler import scheduler
from src.config.settings import settings
from src.orders.dependencies import valid_ordered_product, valid_order_info
from src.orders.schemas import ProductInCartCreate, OrderCreate, OrderResponse, OrderNumerResponse, ProductInCartResponse
from src.orders.services import gen_order_number, valid_equal_coffee_house, \
    cart2order

router = APIRouter(prefix='/api')


@router.post('/add_prod2cart',
             tags=['jwt require', 'orders'],
             description='Для добавления продукта в корзину',
             status_code=status.HTTP_200_OK)
def add_prod2cart(
        product_to_order: Annotated[ProductInCartCreate, Depends(valid_ordered_product)],
        customer: Annotated[Customer, Depends(get_current_active_user)],
        db: Annotated[Session, Depends(get_db)]):
    prod_in_cart = ProductInCart(
        customer_phone_number=customer.phone_number,
        product_various_id=product_to_order.product_various_id,
    )
    prod_in_cart.save(db)

    for top_id in product_to_order.toppings:
        top2prod = Topping2ProductInCart(
            product_in_cart_id=prod_in_cart.id,
            topping_id=top_id
        )
        top2prod.save(db)

    return 'Success'


@router.post('/make_order',
             dependencies=[Depends(valid_timeout_between_orders)],
             tags=['jwt require', 'orders'],
             description='Служит для создания заказа',
             status_code=status.HTTP_200_OK,
             response_model=OrderNumerResponse)
async def make_order(
        order_info: Annotated[OrderCreate, Depends(valid_order_info)],
        customer: Annotated[Customer, Depends(get_not_baned_user)],
        db: Annotated[Session, Depends(get_db)]):
    prods_in_cart: list[ProductInCart] = customer.cart
    if not prods_in_cart:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Корзина пуста')
    elif not valid_equal_coffee_house(prods_in_cart):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Продукты принадлежат разным кофейням')

    order = Order(
        order_number=gen_order_number(db),
        coffee_house_branch_id=order_info.coffee_house_branch_id,
        customer_phone_number=customer.phone_number,
        comment=order_info.comment,
        time=order_info.time,
    )
    order.save(db)
    cart2order(customer, order, db)

    scheduler.add_job(send_order,
                      'date',
                      timezone='utc',
                      run_date=datetime.utcnow() + settings.time_to_cancel_order,
                      replace_existing=True,
                      args=[order.id],
                      id=str(order.id))
    return {
        'order_number': order.order_number,
        'order_id': order.id,
    }


@router.put('/cancel_order',
            tags=['jwt require', 'orders'],
            description='Служит для отмены заказа')
async def cancel_order(
        order_id: Annotated[int, Body(embed=True)],
        customer: Annotated[Customer, Depends(get_current_active_user)],
        db: Annotated[Session, Depends(get_db)]):
    if db.query(Order).filter_by(id=order_id, customer_phone_number=customer.phone_number).delete() == 0:
        raise HTTPException(status_code=400, detail='Заказ не найден.')
    try:
        scheduler.remove_job(str(order_id))
        db.commit()
        return 'Ok'
    except JobLookupError:
        raise HTTPException(status_code=400, detail='Отменить заказ уже нельзя.')


@router.get('/last_order',
            tags=['jwt require', 'orders'],
            description='Возвращает последний заказ пользователя',
            response_model=OrderResponse)
async def get_last_order(
        customer: Annotated[Customer, Depends(get_current_active_user)],
        db: Annotated[Session, Depends(get_db)]):
    order = db.query(Order).filter_by(customer_phone_number=customer.phone_number).order_by(Order.id.desc()).first()
    if order is None:
        return None
    return OrderResponse.to_dict(order)


@router.get('/order_status/{order_id}',
            tags=['jwt require', 'orders'],
            description='Возвращает статус заказа по его id или ошибку, если заказа нет',
            response_description=' | '.join(item.value for item in OrderStatuses))
async def order_status(
        order_id: Annotated[int, Path()],
        customer: Annotated[Customer, Depends(get_current_active_user)],
        db: Annotated[Session, Depends(get_db)]):
    order: Order = db.query(Order).filter_by(id=order_id).one_or_none()
    if order is None:
        raise HTTPException(status_code=400, detail="Неверный номер заказа")
    if order.customer_phone_number != customer.phone_number:
        raise HTTPException(status_code=400, detail="Это заказ другого пользователя")
    return order.get_status_name()


@router.get('/active_orders',
            tags=['jwt require', 'orders'],
            description='Возвращает активные заказы пользователя',
            response_model=list[OrderResponse])
async def get_active_orders(
        customer: Annotated[Customer, Depends(get_current_active_user)],
        db: Annotated[Session, Depends(get_db)]):
    active_statuses = (OrderStatuses.waiting, OrderStatuses.accepted, OrderStatuses.ready)
    orders = db.query(Order) \
        .filter(Order.customer_phone_number == customer.phone_number, Order.status.in_(active_statuses)) \
        .order_by(Order.id.desc()) \
        .all()
    return (OrderResponse.to_dict(order) for order in orders)


@router.get('/my_orders',
            tags=['jwt require', 'orders'],
            description="Возвращает историю заказов",
            response_model=list[OrderResponse])
async def get_my_order_history(
        customer: Annotated[Customer, Depends(get_current_active_user)]):
    return (OrderResponse.to_dict(order) for order in customer.orders)


@router.get('/my_cart',
            tags=['jwt require', 'orders'],
            description='Возвращает корзину',
            response_model=list[ProductInCartResponse])
async def my_cart(
        customer: Annotated[Customer, Depends(get_current_active_user)]):
    result = []
    prod: ProductInCart
    top: Topping2ProductInCart
    for prod in customer.cart:
        result.append({
            "product_various_id": prod.product_various_id,
            "name": prod.product_various.product.name,
            "description": prod.product_various.product.description,
            "type": prod.product_various.product.type_name,
            "price": prod.product_various.price,
            "size": prod.product_various.size_name,
            "toppings": [
                {
                    "id": top.topping_id,
                    "name": top.topping.name,
                    "price": top.topping.price
                }
                for top in prod.toppings
            ]
        })
    return result