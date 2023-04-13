import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (Column, Boolean, BigInteger, Integer, String, Enum, DateTime, ForeignKey, Time)
from sqlalchemy.orm import relationship, Session

import db
from db import Base, engine


# todo засунуть в Base и переписать
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
    id = None
    phone_number = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(20))
    confirmed = Column(Boolean(False))
    telegram_id = Column(BigInteger, nullable=True)
    chat_id = Column(BigInteger, nullable=True)

    orders = relationship('Order', back_populates='customer')
    ban = relationship("BlackList", uselist=False)

    def __str__(self):
        return f'<{self.name=}, {self.phone_number=}, {self.confirmed=}, {self.telegram_id=}, {self.chat_id=}>'


class CoffeeHouse(Base):
    id = None
    name = Column(String(20), primary_key=True, index=True)
    is_active = Column(Boolean(True))


class CoffeeHouseBranch(Base):
    placement = Column(String(20))
    chat_id = Column(BigInteger)
    is_active = Column(Boolean(True))
    coffee_house_name = Column(ForeignKey('coffeehouses.name', ondelete='CASCADE'))

    worktime = relationship('Worktime')


class ProductType(Base):
    id = None
    name = Column(String(20), primary_key=True, index=True)


class Product(Base):
    name = Column(String(50))
    description = Column(String(200), nullable=True)
    is_active = Column(Boolean(True))
    type_name = Column(ForeignKey('producttypes.name', ondelete='RESTRICT'))
    coffee_house_name = Column(ForeignKey('coffeehouses.name', ondelete='CASCADE'))

    variations = relationship('ProductVarious', back_populates='product')  # One to Many (ForeignKey in related)

    def __str__(self):
        return f'<{self.name=}>'


class ProductSize(Base):
    id = None
    name = Column(String(4), primary_key=True, index=True)


class ProductVarious(Base):
    __tablename__ = 'productvarious'

    price = Column(Integer)
    product_id = Column(ForeignKey('products.id', ondelete='CASCADE'))
    size_name = Column(ForeignKey('productsizes.name', ondelete='RESTRICT'))

    product = relationship('Product', back_populates='variations')


class Topping(Base):
    name = Column(String(100))
    price = Column(Integer)
    is_active = Column(Boolean(True))
    coffee_house_name = Column(ForeignKey('coffeehouses.name', ondelete='CASCADE'))


class OrderStatuses(enum.Enum):
    waiting = 'В ожидании'
    accepted = 'Принят в работу'
    rejected = 'Отклонен'
    taken = 'Отдан покупателю'
    no_taken = 'Не забран покупателем'
    ready = 'Готов'
    cart = 'В корзине'


class Order(Base):
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    order_number = Column(String(3), nullable=True)
    coffee_house_branch_id = Column(ForeignKey('coffeehousebranchs.id', ondelete='SET NULL'), nullable=True)
    customer_phone_number = Column(ForeignKey('customers.phone_number', ondelete='SET NULL'), nullable=True)
    comment = Column(String(200), nullable=True)
    time = Column(DateTime(timezone=True))
    creation_time = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(OrderStatuses), default=OrderStatuses.waiting)
    cancel_reason = Column(String(150), nullable=True)

    customer = relationship('Customer', back_populates='orders')
    coffee_house = relationship('CoffeeHouse')
    ordered_products = relationship('OrderedProduct')

    def get_status_name(self):
        return self.status.value if self.cancel_reason is None else self.cancel_reason

    # todo переписать
    # def save(self, *args, **kwargs):
    #     super(Order, self).save(*args, **kwargs)
    #     if self.status == 4:
    #         if len(self.customer.customer_orders.where(Order.status == 4)) >= 2:
    #             ban_customer(self.customer, datetime.utcnow(), forever=True)


class OrderedProduct(Base):
    order_id = Column(ForeignKey('orders.id', ondelete='CASCADE'))
    product_various_id = Column(ForeignKey('productvarious.id', ondelete='CASCADE'))

    product_various = relationship('ProductVarious')
    toppings = relationship('ToppingToProduct')


class ToppingToProduct(Base):
    ordered_product_id = Column(ForeignKey('orderedproducts.id', ondelete='CASCADE'))
    topping_id = Column(ForeignKey('toppings.id', ondelete='CASCADE'))

    topping = relationship('Topping')


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

    coffee_house_branch_id = Column(ForeignKey('coffeehousebranchs.id', ondelete='CASCADE'))
    day_of_week = Column(Enum(DaysOfWeek))
    open_time = Column(Time)
    close_time = Column(Time)


class LoginCode(Base):
    id = None
    code = Column(Integer, primary_key=True, index=True)
    customer_phone_number = Column(ForeignKey('customers.phone_number', ondelete='CASCADE'))
    expire = Column(DateTime)

    customer = relationship('Customer')  # Many to One (ForeignKey here)


class BlackList(Base):
    __tablename__ = 'blacklist'

    id = None
    customer = Column(ForeignKey('customers.phone_number', ondelete='CASCADE'), primary_key=True, index=True)
    expire = Column(Time, nullable=True)  # если null - это бан навсегда ???


class FSM(Base):
    __tablename__ = 'fsm'

    telegram_id = Column(BigInteger, unique=True)
    state = Column(Integer, nullable=True)


class MenuUpdateTime(Base):
    time = Column(DateTime)
    coffee_house_name = Column()


__all__ = ['Customer', 'CoffeeHouse', 'CoffeeHouseBranch', 'ProductType', 'Product', 'ProductSize', 'ProductVarious',
           'Topping', 'OrderStatuses', 'Order', 'OrderedProduct', 'ToppingToProduct', 'DaysOfWeek', 'Worktime',
           'LoginCode', 'BlackList', 'FSM', 'MenuUpdateTime']

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
