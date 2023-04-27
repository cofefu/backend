import requests
import json

from fastapiProject.settings import settings
from payment.schemas import SbisAuthTokens


def sbis_authorization() -> SbisAuthTokens:
    data = {
        "app_client_id": settings.sbis_app_client_id,
        "app_secret": settings.sbis_app_secret,
        "secret_key": settings.sbis_secret_key
    }
    url = 'https://online.sbis.ru/oauth/service/'
    response = requests.post(url, json=data)
    response.encoding = 'utf-8'
    return SbisAuthTokens(**json.loads(response.text))


def get_sales_points(tokens: SbisAuthTokens):
    url = 'https://api.sbis.ru/retail/point/list'
    response = requests.get(url, headers={'X-SBISAccessToken': tokens.access_token})
    return [sale_point['id'] for sale_point in json.loads(response.text)['salesPoints']]


def get_nomenclature(tokens: SbisAuthTokens, point_id: int):
    url = 'https://api.sbis.ru/retail/nomenclature/list'
    headers = {'X-SBISAccessToken': tokens.access_token}
    response = requests.get(url, headers=headers, params={'pointId': point_id})
    print(json.loads(response.text))


def create_order(tokens: SbisAuthTokens, point_id: int):
    url = "https://api.sbis.ru/retail/order/create"

    payload = json.dumps({
        "product": "delivery",
        "pointId": point_id,
        "comment": "as fast as possible",
        "customer": {
            "externalId": None,
            "name": "Алексей",
            "lastname": "Алексеев",
            "patronymic": "Алексеевич",
            "email": "alex@post.com",
            "phone": "88005553535"
        },
        "datetime": "2021-05-07 16:33:34",
        "nomenclatures": [
            {
                "externalId": "88b78352-49f3-479c-8d0f-5064eb75c215",
                "priceListId": 7499,
                "count": 1,
                "cost": 115
            }
        ],
        "delivery": {
            "addressFull": "г. Уфа, ул. Менделеева, д. 134/7",
            "addressJSON": "{\"City\": \"г. Уфа\", \"Street\": \"ул. Менделеева\", \"HouseNum\": \"д.134/7\"}",
            "paymentType": "card",
            "persons": 4,
            "isPickup": False
        }
    })
    headers = {
        'X-SBISAccessToken': tokens.access_token,
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)
