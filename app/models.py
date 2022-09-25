import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (Column, Boolean, BigInteger, Integer, String, Enum, DateTime, ForeignKey,
                        CheckConstraint, Time)
from sqlalchemy.orm import relationship
import sqlalchemy

import db
from db import Base, engine


class Customer(Base):
    name = Column(String(20))
    phone_number = Column(String(10))
    confirmed = Column(Boolean(False))
    orders = relationship('Order')
    telegram_id = Column(BigInteger, nullable=True)
    chat_id = Column(BigInteger, nullable=True)

    @property  # REDO
    def ban(self):
        return self.bans.get_or_none()

    def __str__(self):
        return f'<{self.name=}, {self.phone_number=}, {self.confirmed=}, {self.telegram_id=}, {self.chat_id=}>'


class Product(Base):
    type = Column(Integer, nullable=False)
    variations = relationship('ProductVarious')  # One to Many (ForeignKey in related)
    name = Column(String(50))
    description = Column(String(200), nullable=True)
    img = Column(String(200), nullable=True)

    def __str__(self):
        return f'name: {self.name}'

    def get_type_name(self):
        return 'Not implemented'


class ProductVarious(Base):
    __tablename__ = 'productvarious'

    product_id = Column(ForeignKey('products.id', ondelete='CASCADE'))
    size = Column(Integer, CheckConstraint('size >= 0'), nullable=False)  # REDO need constraint?
    price = Column(Integer, CheckConstraint('size >= 0'))

    def get_size_name(self):
        return 'Not implemented'


class Order(Base):
    coffee_house_id = Column(Integer, ForeignKey('coffeehouses.id', ondelete='SET NULL'), nullable=True)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='SET NULL'), nullable=True)
    ordered_products = relationship('OrderedProduct')
    comment = Column(String(200), nullable=True)
    time = Column(Time)
    creation_time = Column(DateTime, default=datetime.utcnow)
    status = Column(
        # Enum(
        #     'В ожидании',
        #     'Принят в работу',
        #     'Отклонен',
        #     'Отдан покупателю',
        #     'Не забран покупателем',
        #     'Готов'
        # ),
        Integer, nullable=False,
        default=0
    )

    def get_status_name(self):
        if self.status == 2:
            return 'Отклонен' if (reason := self.cancel_reason.get_or_none()) is None else reason.reason
        return dict(self.OrderStatus)[self.status]

    # def save(self, *args, **kwargs):
    #     super(Order, self).save(*args, **kwargs)
    #     if self.status == 4:
    #         if len(self.customer.customer_orders.where(Order.status == 4)) >= 2:
    #             ban_customer(self.customer, datetime.utcnow(), forever=True)


class OrderedProduct(Base):
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'))
    product_id = Column(Integer, ForeignKey('productvarious.id', ondelete='CASCADE'))
    product = relationship('ProductVarious')


class CoffeeHouse(Base):
    name = Column(String(20))
    placement = Column(String(20))
    # worktime = relationship('Worktime')
    chat_id = Column(BigInteger)
    is_open = Column(Boolean)


class Worktime(Base):
    # __tablename__ = 'worktime'
    coffee_house = Column(Integer, ForeignKey('coffeehouses.id', ondelete='CASCADE'))
    day_of_week = Column(
        # Enum(
        #     'Понедельник',
        #     'Вторник',
        #     'Среда',
        #     'Четверг',
        #     'Пятница',
        #     'Суббота',
        #     'Воскресенье',
        # )
        Integer, nullable=False
    )
    open_time = Column(Time)
    close_time = Column(Time)

    def get_day_of_week_name(self):
        return dict(self.DaysOfWeek)[self.day_of_week]


class Topping(Base):
    name = Column(String(100))
    price = Column(Integer, CheckConstraint('price >= 0'))


class ToppingToProduct(Base):
    ordered_product = Column(Integer, ForeignKey('orderedproduct', ondelete='CASCADE'))
    # backref = 'toppings'
    topping = Column(Integer, ForeignKey('toppings', ondelete='CASCADE'))


class LoginCode(Base):
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='CASCADE'))
    customer = relationship('Customer')  # Many to One (ForeignKey here)
    code = Column(Integer, unique=True)
    expire = Column(Time)


class BlackList(Base):
    customer = Column(Integer, ForeignKey('customers', ondelete='CASCADE'), unique=True)
    # backref = 'bans'
    expire = Column(Time, nullable=True)  # если null - это бан навсегда ???
    forever = Column(Boolean, default=False)


class OrderCancelReason(Base):
    order = Column(Integer, ForeignKey('orders', ondelete='CASCADE'), unique=True)
    # backref = 'cancel_reason'
    reason = Column(String(150))


class FSM(Base):
    telegram_id = Column(BigInteger, unique=True)
    state = Column(Integer, nullable=True)


class MenuUpdateTime(Base):
    time = Column(DateTime)


__all__ = ['Customer', 'Product', 'CoffeeHouse', 'Order', 'Worktime', 'ProductVarious', 'OrderedProduct',
           'ToppingToProduct', 'Topping', 'LoginCode', 'BlackList', 'ban_customer', 'OrderCancelReason', 'FSM',
           'MenuUpdateTime']

# TODO remove
if __name__ == '__main__':
    ses = db.SessionLocal()
    print(ses.query(Order).filter_by(id=37).delete())
    ses.commit()


# todo перенести куда-нибудь эту функцию
def ban_customer(customer: Customer, expire: datetime, forever: bool = False) -> Optional[BlackList]:
    if customer is None:
        return

    ban: BlackList = customer.ban
    if ban is None:
        return BlackList.create(customer=customer, expire=expire, forever=forever)

    if forever:
        ban.forever = forever
        ban.save()
        return ban

    if ban.expire < expire:
        ban.expire = expire
        ban.save()
        return ban

    return ban
