from fastapi.testclient import TestClient
from fastapiProject.main import app

client = TestClient(app, base_url='/api')


def test_get_products():
    response = client.get('/products')
    assert response.status_code == 200


def test_get_coffee_houses():
    response = client.get('/coffee_houses')
    assert response.status_code == 200


def test_get_order_status():
    response = client.get('/order_status')
    assert response.status_code == 200


def test_get_products_various():
    response = client.get('/products_various/1')
    assert response.status_code == 200


def test_get_toppings():
    response = client.get('/products_various/1')
    assert response.status_code == 200


# def test_get_favicon_svg():
#     response = client.get('/')
#     assert response.status_code == 200


# def test_get_favicon_ico():
#     response = client.get('/')
#     assert response.status_code == 200


def test_post_make_order():
    response = client.post('/make_order')
    assert response.status_code == 200


def test_post_register_customer():
    response = client.post('/register_customer')
    assert response.status_code == 200


def test_post_update_token():
    response = client.post('/update_token')
    assert response.status_code == 200


def test_post_send_login_code():
    response = client.post('/send_login_code')
    assert response.status_code == 200


def testp_get_verify_login_code():
    response = client.get('/verify_login_code')
    assert response.status_code == 200


def test_get_my_orders():
    response = client.get('/my_orders')
    assert response.status_code == 200


def test_get_me():
    response = client.get('/me')
    assert response.status_code == 200


def test_get_last_order():
    response = client.get('/last_order')
    assert response.status_code == 200
