from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_products():
    responce = client.get('/products')
    assert response.status_code == 200


def test_get_coffee_houses():
    responce = client.get('/coffee_houses')
    assert response.status_code == 200


def test_get_order_status():
    responce = client.get('/order_status')
    assert response.status_code == 200


def test_get_products_various():
    responce = client.get('/products_various/1')
    assert response.status_code == 200


def test_get_toppings():
    responce = client.get('/products_various/1')
    assert response.status_code == 200


# def test_get_favicon_svg():
#     responce = client.get('/')
#     assert response.status_code == 200


# def test_get_favicon_ico():
#     responce = client.get('/')
#     assert response.status_code == 200


def test_post_make_order():
    responce = client.post('/make_order')
    assert response.status_code == 200


def test_post_register_customer():
    responce = client.post('/register_customer')
    assert response.status_code == 200


def test_post_update_token():
    responce = client.post('/update_token')
    assert response.status_code == 200


def test_post_send_login_code():
    responce = client.post('/send_login_code')
    assert response.status_code == 200


def testp_get_verify_login_code():
    responce = client.get('/verify_login_code')
    assert response.status_code == 200


def test_get_my_orders():
    responce = client.get('/my_orders')
    assert response.status_code == 200


def test_get_me():
    responce = client.get('/me')
    assert response.status_code == 200


def test_get_last_order():
    responce = client.get('/last_order')
    assert response.status_code == 200
