from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.utils import get_random_order


def test_get_products(client: TestClient):
    response = client.get('api/products')
    assert response.status_code == 200


def test_get_coffee_houses(client: TestClient):
    response = client.get('api/coffee_houses')
    assert response.status_code == 200


def test_get_existing_order_status(client: TestClient, db: Session):
    if order := get_random_order(db):
        response = client.get(f'/order_status/{order.id}')
        assert response.status_code == 200
        assert response.json == order.get_status_name()


def test_get_products_various(client: TestClient):
    response = client.get('/products_various/1')
    assert response.status_code == 200


def test_get_toppings(client: TestClient):
    response = client.get('/products_various/1')
    assert response.status_code == 200


# def test_get_favicon_svg():
#     response = client.get('/')
#     assert response.status_code == 200


# def test_get_favicon_ico():
#     response = client.get('/')
#     assert response.status_code == 200


def test_post_make_order(client: TestClient):
    response = client.post('/make_order')
    assert response.status_code == 200


def test_post_register_customer(client: TestClient):
    response = client.post('/register_customer')
    assert response.status_code == 200


def test_post_update_token(client: TestClient):
    response = client.post('/update_token')
    assert response.status_code == 200


def test_post_send_login_code(client: TestClient):
    response = client.post('/send_login_code')
    assert response.status_code == 200


def testp_get_verify_login_code(client: TestClient):
    response = client.get('/verify_login_code')
    assert response.status_code == 200


def test_get_my_orders(client: TestClient):
    response = client.get('/my_orders')
    assert response.status_code == 200


def test_get_me(client: TestClient):
    response = client.get('/me')
    assert response.status_code == 200


def test_get_last_order(client: TestClient):
    response = client.get('/last_order')
    assert response.status_code == 200
