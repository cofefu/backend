from datetime import datetime

from peewee import \
    ForeignKeyField, CharField, DateTimeField, IntegerField

from db import BaseModel


class Customer(BaseModel):
    name = CharField(max_length=20)
    phone_number = CharField(max_length=20)
    email = CharField(max_length=100)  # Maybe less characters

    def __str__(self):
        return f'name: {self.name}, phone_number: {self.phone_number}, email: {self.email}'

    class Meta:
        table_name = 'customers'


class Product(BaseModel):
    name = CharField(max_length=20)
    description = CharField(max_length=200, null=True)
    img = CharField(max_length=200)

    def __str__(self):
        return f'name: {self.name}'

    class Meta:
        table_name = 'products'


class CoffeeHouse(BaseModel):
    name = CharField(max_length=20)
    placement = CharField(max_length=20)
    chat_id = IntegerField()

    def __str__(self):
        return f'name: {self.name}, placement: {self.placement}'

    class Meta:
        table_name = 'coffeehouses'


STATUS = (
    (0, 'None'),
    (1, 'Accept'),
    (2, 'Work'),
    (3, 'Ready')
)


class Order(BaseModel):
    coffee_house = ForeignKeyField(CoffeeHouse, backref='coffee_house')
    customer = ForeignKeyField(Customer, backref='customer')
    product = ForeignKeyField(Product, related_name='products')
    time = DateTimeField()
    status = IntegerField(choices=STATUS, default=0)

    class Meta:
        table_name = 'orders'


if __name__ == '__main__':
    import db

    db.db.create_tables([Customer, Product, CoffeeHouse, Order, ])

__all__ = ['Customer', 'Product', 'CoffeeHouse', 'Order']
