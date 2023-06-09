from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models import Customer, Order, ProductInCart


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



def gen_order_number() -> str:
    """
    Генерирует номер заказа.
    :return order number: A54
    """
    pass


async def valid_equal_coffee_house(prods_in_cart: list[ProductInCart]) -> bool:
    """
    Проверяет, что продукты в заказе относятся к одной кофейне. Возможно рэйзит ошибку
    :param prods_in_cart: list of integer of ProductInCart model
    :rtype: bool
    """
    pass
