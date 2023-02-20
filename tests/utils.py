from sqlalchemy.orm import Session
from app.models import Order, Customer, Product, ProductVarious, Topping, ProductTypes, ProductSizes, CoffeeHouse, \
    DaysOfWeek, Worktime


def get_random_order(db: Session) -> Order:
    return db.query(Order).first()


def get_or_create_customer(db: Session) -> Customer:
    if customer := db.query(Customer).first():
        return customer
    new_customer = Customer(
        name='test customer',
        phone_number='9998887745',
        confirmed=True,
        telegram_id=0,
        chat_id=0
    )
    new_customer.save(db)
    return new_customer


def get_or_create_product(db: Session) -> Product:
    """Возвращает продукт. Если создает, то создает и его вариации"""
    if prod := db.query(Product).first():
        return prod
    new_prod = Product(
        type=ProductTypes.coffee,
        name='Какой-то напиток',
        description='Описание продукта',
    )
    new_prod.save(db)
    get_or_create_product_various(db, new_prod)
    return new_prod


def get_or_create_product_various(db: Session, prod: Product) -> ProductVarious:
    if prod_var := db.query(ProductVarious).filter_by(product_id=prod.id).first():
        return prod_var
    new_prod_var = ProductVarious(
        product_id=prod.id,
        size=ProductSizes.S,
        price=100
    )
    new_prod_var.save(db)
    return new_prod_var


def get_or_create_topping(db: Session) -> Topping:
    if topping := db.query(Topping).first():
        return topping
    new_topping = Topping(
        name='Какой-то топпинг',
        price=30
    )
    new_topping.save(db)
    return new_topping


def get_or_create_coffee_house(db: Session) -> CoffeeHouse:
    """Возвращает кофейню. Если создает ее, то создает и рабочее время"""
    if ch := db.query(CoffeeHouse).first():
        return ch
    new_ch = CoffeeHouse(
        name='Крутая кофейня',
        placement='Тут адрес',
        chat_id=0,
        is_open=True
    )
    new_ch.save(db)
    for day in DaysOfWeek:
        db.add(Worktime(
            coffee_house_id=new_ch.id,
            day_of_week=day,
            open_time="00:00:00",
            close_time="23:59:59"
        ))
    db.commit()
    return new_ch
