from datetime import datetime
from typing import Optional

from peewee import (ForeignKeyField, CharField, DateTimeField, IntegerField,
                    TimeField, BooleanField, Check, TimestampField, BigIntegerField)
from playhouse.postgres_ext import DateTimeTZField

from db import BaseModel


class Customer(BaseModel):
    name = CharField(max_length=20)
    phone_number = CharField(max_length=10)
    confirmed = BooleanField(default=False)
    telegram_id = BigIntegerField(null=True)
    chat_id = BigIntegerField(null=True)

    @property
    def ban(self):
        return self.bans.get_or_none()

    def __str__(self):
        return f'name: {self.name}, phone_number: {self.phone_number}'

    class Meta:
        table_name = 'customers'


class Product(BaseModel):
    ProductTypes = (
        (0, 'Кофе'),
        (1, 'Не кофе'),
        (2, 'Летнее'),
    )
    type = IntegerField(choices=ProductTypes, default=0)
    name = CharField(max_length=50)
    description = CharField(max_length=200, null=True)
    img = CharField(max_length=200, null=True)

    class Meta:
        table_name = 'products'

    def __str__(self):
        return f'name: {self.name}'

    def get_type_name(self):
        return dict(self.ProductTypes)[self.type]


class ProductVarious(BaseModel):
    ProductSizes = (
        (0, 'S'),
        (1, 'M'),
        (2, 'L')
    )
    product = ForeignKeyField(Product, backref='variations', on_delete='CASCADE')
    size = IntegerField(choices=ProductSizes, constraints=[Check('size >= 0')])
    price = IntegerField(constraints=[Check('size >= 0')])

    def get_size_name(self):
        return dict(self.ProductSizes)[self.size]


class CoffeeHouse(BaseModel):
    name = CharField(max_length=20)
    placement = CharField(max_length=20)
    chat_id = BigIntegerField()
    is_open = BooleanField()

    def __str__(self):
        return f'name: {self.name}, placement: {self.placement}'

    class Meta:
        table_name = 'coffeehouses'


class Order(BaseModel):
    OrderStatus = (
        (0, 'В ожидании'),
        (1, 'Принят в работу'),
        (2, 'Отклонен'),
        (3, 'Отдан покупателю'),
        (4, 'Не забран покупателем'),
        (5, 'Готов')
    )
    coffee_house = ForeignKeyField(CoffeeHouse, backref='house_orders', null=True, on_delete='SET NULL')
    customer = ForeignKeyField(Customer, backref='customer_orders', null=True, on_delete='SET NULL')
    comment = CharField(max_length=200, null=True)
    time = DateTimeTZField()
    creation_time = DateTimeField(default=datetime.utcnow)
    status = IntegerField(default=0, choices=OrderStatus)

    class Meta:
        table_name = 'orders'

    def get_status_name(self):
        if self.status == 2:
            return 'Отклонен' if (reason := self.cancel_reason.get_or_none()) is None else reason.reason
        return dict(self.OrderStatus)[self.status]

    def save(self, *args, **kwargs):
        super(Order, self).save(*args, **kwargs)
        if self.status == 4:
            if len(self.customer.customer_orders.where(Order.status == 4)) >= 2:
                ban_customer(self.customer, datetime.utcnow(), forever=True)


class OrderedProduct(BaseModel):
    order = ForeignKeyField(Order, backref='ordered_products', on_delete='CASCADE')
    product = ForeignKeyField(ProductVarious, on_delete='CASCADE')


class Worktime(BaseModel):
    DaysOfWeek = (
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    )
    coffee_house = ForeignKeyField(CoffeeHouse, backref='worktime', on_delete='CASCADE')
    day_of_week = IntegerField(choices=DaysOfWeek)
    open_time = TimeField(formats='%H:%M:%S')
    close_time = TimeField(formats='%H:%M:%S')

    def get_day_of_week_name(self):
        return dict(self.DaysOfWeek)[self.day_of_week]


class Topping(BaseModel):
    name = CharField(max_length=100)
    price = IntegerField(constraints=[Check('price >= 0')])


class ToppingToProduct(BaseModel):
    ordered_product = ForeignKeyField(OrderedProduct, backref='toppings', on_delete='CASCADE')
    topping = ForeignKeyField(Topping, on_delete='CASCADE')


class LoginCode(BaseModel):
    customer = ForeignKeyField(Customer, on_delete='CASCADE')
    code = IntegerField(unique=True)
    expire = TimestampField()


class BlackList(BaseModel):
    customer = ForeignKeyField(Customer, unique=True, on_delete='CASCADE', backref='bans')
    expire = TimestampField(null=True)  # если null - это бан навсегда ???
    forever = BooleanField(default=False)


class OrderCancelReason(BaseModel):
    order = ForeignKeyField(Order, unique=True, on_delete='CASCADE', backref='cancel_reason')
    reason = CharField(max_length=150)


class FSM(BaseModel):
    telegram_id = BigIntegerField(unique=True)
    state = IntegerField(null=True)


class MenuUpdateTime(BaseModel):
    time = DateTimeField()


# TODO вынести в db.migrate
if __name__ == '__main__':
    import db
    from app import field_db

    db.db.create_tables(
        [Customer, Product, CoffeeHouse, Order, Worktime,
         ProductVarious, OrderedProduct, ToppingToProduct, Topping,
         LoginCode, BlackList, OrderCancelReason, FSM, MenuUpdateTime])

    # field_db.field_all()

__all__ = ['Customer', 'Product', 'CoffeeHouse', 'Order', 'Worktime', 'ProductVarious', 'OrderedProduct',
           'ToppingToProduct', 'Topping', 'LoginCode', 'BlackList', 'ban_customer', 'OrderCancelReason', 'FSM',
           'MenuUpdateTime']


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
