import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (Column, Boolean, BigInteger, Integer, String, Enum, DateTime, ForeignKey,
                        CheckConstraint, Time)
from sqlalchemy.orm import relationship, Session
import sqlalchemy

import db
from db import Base, engine


def get_or_create(session: Session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance, True


class Customer(Base):
    name = Column(String(20))
    phone_number = Column(String(10))
    confirmed = Column(Boolean(False))
    telegram_id = Column(BigInteger, nullable=True)
    chat_id = Column(BigInteger, nullable=True)

    orders = relationship('Order', back_populates='customer')
    ban = relationship("BlackList", uselist=False)

    def __str__(self):
        return f'<{self.name=}, {self.phone_number=}, {self.confirmed=}, {self.telegram_id=}, {self.chat_id=}>'


class ProductTypes(enum.Enum):
    coffee = 'Кофе'
    no_coffee = 'Не кофе'
    special = 'Special'


class Product(Base):
    type = Column(Enum(ProductTypes))
    name = Column(String(50))
    description = Column(String(200), nullable=True)
    img = Column(String(200), nullable=True)

    variations = relationship('ProductVarious', back_populates='product')  # One to Many (ForeignKey in related)

    def __str__(self):
        return f'<{self.name=}>'


class ProductSizes(enum.Enum):
    S = 'S'
    M = 'M'
    L = 'L'


class ProductVarious(Base):
    __tablename__ = 'productvarious'

    product_id = Column(ForeignKey('products.id', ondelete='CASCADE'))
    size = Column(Enum(ProductSizes))
    price = Column(Integer)

    product = relationship('Product', back_populates='variations')


class OrderStatuses(enum.Enum):
    waiting = 'В ожидании'
    accepted = 'Принят в работу'
    rejected = 'Отклонен'
    taken = 'Отдан покупателю'
    no_taken = 'Не забран покупателем'
    ready = 'Готов'


class Order(Base):
    coffee_house_id = Column(Integer, ForeignKey('coffeehouses.id', ondelete='SET NULL'), nullable=True)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='SET NULL'), nullable=True)
    comment = Column(String(200), nullable=True)
    time = Column(DateTime(timezone=True))
    creation_time = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(OrderStatuses), default=OrderStatuses.waiting)

    customer = relationship('Customer', back_populates='orders')
    coffee_house = relationship('CoffeeHouse')
    ordered_products = relationship('OrderedProduct')
    cancel_reason = relationship("OrderCancelReason", uselist=False)

    def get_status_name(self):
        return self.status.value if self.cancel_reason is None else self.cancel_reason.reason

    # todo переписать
    # def save(self, *args, **kwargs):
    #     super(Order, self).save(*args, **kwargs)
    #     if self.status == 4:
    #         if len(self.customer.customer_orders.where(Order.status == 4)) >= 2:
    #             ban_customer(self.customer, datetime.utcnow(), forever=True)


class OrderedProduct(Base):
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'))
    product_id = Column(Integer, ForeignKey('productvarious.id', ondelete='CASCADE'))

    product = relationship('ProductVarious')
    toppings = relationship('ToppingToProduct')


class CoffeeHouse(Base):
    name = Column(String(20))
    placement = Column(String(20))
    chat_id = Column(BigInteger)
    is_open = Column(Boolean)

    worktime = relationship('Worktime')


class DaysOfWeek(enum.Enum):
    monday = 0
    tuesday = 1
    wednesday = 2
    thursday = 3
    friday = 4
    saturday = 5
    sunday = 6


class Worktime(Base):
    __tablename__ = 'worktime'

    coffee_house_id = Column(Integer, ForeignKey('coffeehouses.id', ondelete='CASCADE'))
    day_of_week = Column(Enum(DaysOfWeek))
    open_time = Column(Time)
    close_time = Column(Time)


class Topping(Base):
    name = Column(String(100))
    price = Column(Integer, CheckConstraint('price >= 0'))


# todo maybe change to ARRAY(Integer) in OrderedProduct
class ToppingToProduct(Base):
    ordered_product_id = Column(Integer, ForeignKey('orderedproducts.id', ondelete='CASCADE'))
    topping_id = Column(Integer, ForeignKey('toppings.id', ondelete='CASCADE'))

    topping = relationship('Topping')


class LoginCode(Base):
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='CASCADE'))
    code = Column(Integer, unique=True)
    expire = Column(DateTime)

    customer = relationship('Customer')  # Many to One (ForeignKey here)


class BlackList(Base):
    __tablename__ = 'blacklist'

    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='CASCADE'), unique=True)
    expire = Column(Time, nullable=True)  # если null - это бан навсегда ???
    forever = Column(Boolean, default=False)


class OrderCancelReason(Base):
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'), unique=True)
    reason = Column(String(150))


class FSM(Base):
    __tablename__ = 'fsm'

    telegram_id = Column(BigInteger, unique=True)
    state = Column(Integer, nullable=True)


class MenuUpdateTime(Base):
    time = Column(DateTime)


__all__ = ['Customer', 'Product', 'CoffeeHouse', 'Order', 'Worktime', 'ProductVarious', 'OrderedProduct',
           'ToppingToProduct', 'Topping', 'LoginCode', 'BlackList', 'ban_customer', 'OrderCancelReason', 'FSM',
           'MenuUpdateTime', 'OrderStatuses', 'ProductTypes', 'ProductSizes']

# TODO remove
if __name__ == '__main__':
    Base.metadata.create_all(engine)


# todo перенести куда-нибудь эту функцию
def ban_customer(customer: Customer, expire: datetime, forever: bool = False) -> Optional[BlackList]:
    if customer is None:
        return

    sess: Session
    with db.SessionLocal() as sess:
        ban: BlackList = customer.ban
        if ban is None:
            new_ban = BlackList(customer_id=customer.id, expire=expire, forever=forever)
            sess.add(new_ban)
            sess.commit()
            return new_ban

        if forever:
            ban.forever = forever
            sess.commit()
            return ban

        if ban.expire < expire:
            ban.expire = expire
            sess.commit()
            return ban

        return ban
