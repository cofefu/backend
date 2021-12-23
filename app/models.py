from datetime import datetime

from peewee import \
    ForeignKeyField, CharField, DateTimeField, BooleanField

from db import BaseModel


class User(BaseModel):
    name = CharField(max_length=20, null=True)
    phone_number = CharField(max_length=20)
    password = CharField(max_length=100)

    def __str__(self):
        return f'{self.name = }, {self.phone_number = }'

    class Meta:
        hidden_fields = ['password']
        table_name = 'users'


class Product(BaseModel):
    name = CharField(max_length=20)
    description = CharField(max_length=200, null=True)
    img = CharField(max_length=200)
    has_additions = BooleanField(default=False)

    def __str__(self):
        return f'{self.name = }, {self.has_additions = }, {self.description = }'

    class Meta:
        table_name = 'products'


class CoffeeHouse(BaseModel):
    name = CharField(max_length=20)
    placement = CharField(max_length=20)

    def __str__(self):
        return f'{self.name = }, {self.placement = }'

    class Meta:
        table_name = 'coffeehouses'


class Order(BaseModel):
    coffee_house = ForeignKeyField(CoffeeHouse, backref='coffee_house')
    customer = ForeignKeyField(User, backref='customer')
    product = ForeignKeyField(Product, related_name='products')
    time = DateTimeField()

    def __str__(self):
        return f"{self.coffee_house: }, {self.customer: }, {self.product = }, {self.time = }"

    class Meta:
        table_name = 'orders'


class Feedback(BaseModel):
    user = ForeignKeyField(User, backref='customer')
    text = CharField(max_length=250)
    time = DateTimeField(default=datetime.now())

    def __str__(self):
        return f"{self.user: }, {self.feedback = }, {self.time = }"

    class Meta:
        table_name = 'feedbacks'


if __name__ == '__main__':
    import db

    db.db.create_tables([User, Product, CoffeeHouse, Order, Feedback])
