from sqlalchemy import text, create_engine
from src.db.models import *
from src.db.models import get_or_create
from src.db import SessionLocal

import os
from dotenv import load_dotenv

load_dotenv()

old_engine = create_engine(os.getenv('OLD_DB_URL'))

product_types = {'coffee': 'Кофе', 'no_coffee': 'Не кофе'}

def fill_db():
    with SessionLocal() as sess:
        cafe = get_or_create(sess, CoffeeHouse, name='Полка кофе')[0]

        # fill coffee_house_branches and worktime
        with old_engine.connect() as conn:
            command = 'select placement, chat_id, is_open as is_active from coffeehouses order by id'
            for branch_info in conn.execute(text(command)).all():
                branch = get_or_create(sess, CoffeeHouseBranch, **branch_info, coffee_house_name=cafe.name)[0]

                # fill worktime
                command = '''
                    select 
                        day_of_week, open_time, close_time 
                    from worktime 
                    group by day_of_week, open_time, close_time;
                '''
                for day_info in conn.execute(text(command)).all():
                    get_or_create(sess, Worktime, **day_info, coffee_house_branch_id=branch.id)

        # create product_types
        for prod_type in list(product_types.values()):
            get_or_create(sess, ProductType, name=prod_type)
        # create product_sizes
        for prod_size in ('S', 'M', 'L'):
            get_or_create(sess, ProductSize, name=prod_size)

        # fill product and product_various
        with old_engine.connect() as conn:
            command = 'select id, name, description, type as type_name from products order by id'
            for old_prod_info in conn.execute(text(command)).all():
                new_prod_info = dict(old_prod_info)
                del new_prod_info['id']
                new_prod_info['type_name'] = product_types[f'{new_prod_info["type_name"]}']
                prod = get_or_create(sess, Product, **new_prod_info, is_active=True, coffee_house_name=cafe.name)[0]

                # fill product_various
                command = f'select size as size_name, price from productvarious where product_id = {old_prod_info["id"]}'
                for various in conn.execute(text(command)).all():
                    get_or_create(sess, ProductVarious, **various, product_id=prod.id)

        # fill toppings
        with old_engine.connect() as conn:
            command = 'select name, price from toppings order by id'
            for topping in conn.execute(text(command)).all():
                get_or_create(sess, Topping, **topping, is_active=True, coffee_house_name=cafe.name)

        # fill customers
        with old_engine.connect() as conn:
            command = 'select phone_number, name, telegram_id, chat_id from customers'
            for customer in conn.execute(text(command)).all():
                get_or_create(sess, Customer, **customer)