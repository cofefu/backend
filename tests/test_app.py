import random
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from pytz import timezone
from sqlalchemy.orm import Session

from db.models import Customer, LoginCode
from auth.services import create_token
from tests.utils import get_or_create_customer, get_or_create_product, get_or_create_topping, get_or_create_coffee_house, get_or_create_any_customer_order


def test_get_products(client: TestClient):
    response = client.get('api/products')
    assert response.status_code == 200


def test_get_coffee_houses(client: TestClient):
    response = client.get('api/coffee_houses')
    assert response.status_code == 200


def test_get_existing_order_status(client: TestClient, db: Session):
    customer = get_or_create_customer(db)
    order = get_or_create_any_customer_order(db, customer)
    response = client.get(
        f'api/order_status/{order.id}',
        headers={"jwt-token": create_token(customer)},
    )
    assert response.status_code == 200
    assert response.json() == order.get_status_name()


def test_get_products_various(client: TestClient, db: Session):
    product = get_or_create_product(db)
    response = client.get(f'api/products_various/{product.id}')
    assert response.status_code == 200


def test_get_toppings(client: TestClient):
    response = client.get('api/toppings')
    assert response.status_code == 200


# def test_get_favicon_svg():
#     response = client.get('/')
#     assert response.status_code == 200


# def test_get_favicon_ico():
#     response = client.get('/')
#     assert response.status_code == 200


def test_register_new_customer(client: TestClient, db: Session):
    data = {'name': 'test', 'phone_number': '9998884455'}
    response = client.post(
        'api/register_customer',
        json=data,
    )
    new_customer = db.query(Customer).filter_by(phone_number=data['phone_number']).first()
    new_customer.delete(db)
    assert response.status_code == 200


def test_register_existing_customer(client: TestClient, db: Session):
    customer = get_or_create_customer(db)
    response = client.post(
        'api/register_customer',
        json={'name': customer.name, 'phone_number': customer.phone_number},
    )
    assert response.status_code == 400


def test_post_update_token(client: TestClient, db: Session):
    customer = get_or_create_customer(db)
    response = client.post(
        'api/update_token',
        headers={"jwt-token": create_token(customer)},
    )
    assert response.status_code == 200


def test_send_login_code(client: TestClient, db: Session):
    customer = get_or_create_customer(db)
    response = client.post(
        'api/send_login_code_to_telegram',
        json={'name': customer.name, 'phone_number': customer.phone_number},
    )

    if (lc := db.query(LoginCode).filter_by(customer_id=customer.id).first()) is None:
        raise 'Не создался логин код'
    lc.delete(db)
    assert response.status_code == 200


def test_send_login_code_not_exist_customer(client: TestClient, db: Session):
    response = client.post(
        'api/send_login_code_to_telegram',
        json={'name': 'not exist customer', 'phone_number': '1234567890'},
    )
    assert response.status_code == 400


def test_send_login_code_not_confirmed_customer(client: TestClient, db: Session):
    tmp_customer = Customer(name='tmp', phone_number='1111111111')
    tmp_customer.save(db)

    response = client.post(
        'api/send_login_code_to_telegram',
        json={'name': tmp_customer.name, 'phone_number': tmp_customer.phone_number},
    )

    tmp_customer.delete(db)
    assert response.status_code == 401


def test_verify_login_code(client: TestClient, db: Session):
    customer = get_or_create_customer(db)
    code = random.randint(100000, 999999)
    while db.query(LoginCode).filter_by(code=code).one_or_none():
        code = random.randint(100000, 999999)
    lc = LoginCode(customer_id=customer.id, code=code, expire=datetime.utcnow() + timedelta(minutes=5))
    lc.save(db)

    response = client.get(
        'api/verify_login_code',
        params={'code': code},
    )
    lc.delete(db)
    assert response.status_code == 200


def test_verify_incorrect_login_code(client: TestClient):
    response = client.get(
        'api/verify_login_code',
        params={'code': -1},
    )
    assert response.status_code == 401


def test_verify_old_login_code(client: TestClient, db: Session):
    customer = get_or_create_customer(db)
    code = random.randint(100000, 999999)
    while db.query(LoginCode).filter_by(code=code).one_or_none():
        code = random.randint(100000, 999999)
    lc = LoginCode(customer_id=customer.id, code=code, expire=datetime.utcnow() - timedelta(minutes=5))
    lc.save(db)

    response = client.get(
        'api/verify_login_code',
        params={'code': code},
    )
    lc.delete(db)
    assert response.status_code == 401


def test_get_my_orders(client: TestClient, db: Session):
    customer = get_or_create_customer(db)
    response = client.get(
        'api/my_orders',
        headers={"jwt-token": create_token(customer)},
    )
    assert response.status_code == 200


def test_get_me(client: TestClient, db: Session):
    customer = get_or_create_customer(db)
    response = client.get(
        'api/me',
        headers={"jwt-token": create_token(customer)},
    )
    assert response.status_code == 200


def test_last_order(client: TestClient, db: Session):
    customer = get_or_create_customer(db)
    response = client.get(
        'api/last_order',
        headers={"jwt-token": create_token(customer)},
    )
    assert response.status_code == 200


def test_make_order(client: TestClient, db: Session):
    coffee_house = get_or_create_coffee_house(db)
    customer = get_or_create_customer(db)
    product = get_or_create_product(db)
    topping = get_or_create_topping(db)

    response = client.post(
        'api/make_order',
        headers={"jwt-token": create_token(customer)},
        json={
            'coffee_house': coffee_house.id,
            'comment': 'это комментарий',
            'products': [
                {
                    'id': product.id,
                    'toppings': [topping.id, topping.id]
                },
                {
                    'id': product.id,
                    'toppings': []
                },
            ],
            'time': str(datetime.now(tz=timezone('Asia/Vladivostok')) + timedelta(minutes=20))  # redo
        }
    )
    assert response.text == 'hello'
    assert response.status_code == 200


def test_feedback(client: TestClient):
    response = client.post(
        'api/feedback',
        json="Все круто!",
    )
    assert response.status_code == 200


def test_bugreport(client: TestClient, db: Session):
    customer = get_or_create_customer(db)
    response = client.post(
        'api/bugreport',
        json="Ничего не работает",
        headers={"jwt-token": create_token(customer)},
    )
    assert response.status_code == 200


def test_change_name(client: TestClient, db: Session):
    customer = get_or_create_customer(db)
    response = client.put(
        'api/change_name',
        json="andrey",
        headers={"jwt-token": create_token(customer)},
    )
    assert response.status_code == 200


def test_phone_confirmed(client: TestClient, db: Session):
    customer = get_or_create_customer(db)
    response = client.get(
        'api/is_confirmed',
        headers={"jwt-token": create_token(customer)}
    )
    assert response.status_code == 200
    assert bool(response.json) == bool(customer.confirmed)


def test_get_menu(client: TestClient):
    response = client.get(
        'api/menu',
    )
    assert response.status_code == 200
