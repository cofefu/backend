from datetime import datetime, timedelta

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models import Customer, Order, ProductInCart, ProductInOrder, Topping2ProductInOrder, Topping2ProductInCart


def get_or_create_cart(
        customer: Customer,
        db: Session
) -> (Order, bool):
    cart = db.query(Order) \
        .filter_by(customer_phone_number=customer.phone_number) \
        .order_by(desc(Order.id)) \
        .first()
    if cart:
        return cart, False

    cart = Order(customer=customer.phone_number)
    cart.save(db)
    return cart, True


def gen_order_number(
        db: Session
) -> str:
    """
    Генерирует номер заказа.
    :param db: sqlalchemy session
    :return order number: 054
    """
    last_order = db.query(Order).order_by(Order.id.desc()).first()
    if not last_order:
        return '1'
    return str(int(last_order.order_number) / 1000 + 1)


def valid_equal_coffee_house(
        prods_in_cart: list[ProductInCart],
) -> bool:
    """
    Проверяет, что продукты в заказе относятся к одной кофейне.
    :param prods_in_cart: list of integer of ProductInCart model
    :rtype: bool
    """
    for prod in prods_in_cart:
        if prod.product_various.product != prods_in_cart[0].product_various.product:
            return False
    return True


def clear_cart(
        customer: Customer,
        db: Session
) -> None:
    """
    Удаляет все продукты из корзины
    :param customer: customer model
    :param db: sqlalchemy session
    :return:
    """
    prod_in_cart: ProductInCart
    for prod_in_cart in customer.cart:
        prod_in_cart.delete(db)


def cart2order(
        customer: Customer,
        order: Order,
        db: Session
) -> None:
    """
    Copy ProductInCart elements to ProductInOrder with Topping, then clear cart
    :param customer: Customer
    :param order: Order
    :param db: Session
    :return:
    """
    prods_in_cart: list[ProductInCart] = customer.cart
    for prod_in_cart in prods_in_cart:
        prod_in_order = ProductInOrder(
            order_id=order.id,
            product_various_id=prod_in_cart.product_various_id
        )
        prod_in_order.save(db)

        top_in_cart: Topping2ProductInCart
        for top_in_cart in prod_in_cart.toppings:
            top = Topping2ProductInOrder(
                product_in_order_id=prod_in_order.id,
                topping_id=top_in_cart.topping_id
            )
            top.save(db)
    clear_cart(customer, db)


def min_order_preparation_time(
        order_time: datetime
) -> timedelta:
    """
    Calculate min time to prepare order.
    During the break between classes (the busiest time), the minimum cooking time = 10 minutes, otherwise 7 minutes
    :param order_time: time of order issue
    :return: min time to preparation order
    """
    time_breaks = (
        datetime(year=datetime.now().year, month=1, day=1, hour=10),
        datetime(year=datetime.now().year, month=1, day=1, hour=11, minute=40),
        datetime(year=datetime.now().year, month=1, day=1, hour=13, minute=20),
        datetime(year=datetime.now().year, month=1, day=1, hour=15),
        datetime(year=datetime.now().year, month=1, day=1, hour=16, minute=40)
    )

    shift = timedelta(minutes=5)
    for time_break in time_breaks:
        if (time_break - shift).time() < order_time.time() < (time_break + timedelta(minutes=10) + shift).time():
            return timedelta(minutes=10)
    return timedelta(minutes=7)
