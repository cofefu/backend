from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.dependencies import get_db
from app.models import Product, CoffeeHouse, Topping
from menu.dependencies import valid_coffee_house_name
from menu.schemas import ProductsWithTypesResponse, ProductResponseModel, ToppingsResponseModel, \
    CoffeeHouseMenuResponse, CoffeeHouseResponse
from menu.services import coffee_house_branch_worktime_today

router = APIRouter(prefix='/api')


@router.get('/coffee_house_products',
            tags=['common', 'menu'],
            description='Возвращает список продуктов кофейни и его вариации',
            response_model=list[ProductsWithTypesResponse])
async def coffee_house_products(
        coffee_house: Annotated[CoffeeHouse, Depends(valid_coffee_house_name)],
        db: Annotated[Session, Depends(get_db)]):
    result: list[ProductsWithTypesResponse] = []  # возможно выгоднее делать массив словарей
    prev_type_name = ''
    for product in db.query(Product) \
            .where(Product.coffee_house_name == coffee_house.name) \
            .order_by(Product.type_name, Product.id) \
            .all():
        # add new product type
        if prev_type_name != product.type_name:
            result.append(
                ProductsWithTypesResponse(
                    type_name=product.type_name,
                    products=[]
                ))

        product_data = product.data('is_active', 'type_name', 'coffee_house_name')

        # add various of product
        product_vars = (var.data('product_id') for var in product.variations)
        product_data.update({'variations': product_vars})

        # add tags of product
        product_tags = [tag.tag_name for tag in product.tags]
        product_data.update({'tags': product_tags})

        result[-1].products.append(ProductResponseModel(**product_data))
        prev_type_name = product.type_name
    return result


@router.get('/coffee_house_toppings',
            tags=['common', 'menu'],
            description='Возвращает список топингов кофейни',
            response_model=list[ToppingsResponseModel])
async def coffee_house_toppings(
        coffee_house: Annotated[CoffeeHouse, Depends(valid_coffee_house_name)],
        db: Annotated[Session, Depends(get_db)]):
    return [
        top.data('is_active', 'coffee_house_name')
        for top in db.query(Topping).where(Topping.coffee_house_name == coffee_house.name).all()
    ]


@router.get('/coffee_house_menu',
            tags=['common', 'menu'],
            description='Возвращает меню по одной кофейне',
            response_model=CoffeeHouseMenuResponse)
async def coffee_house_menu(
        coffee_house: Annotated[CoffeeHouse, Depends(valid_coffee_house_name)],
        db: Annotated[Session, Depends(get_db)],
        time: Annotated[datetime | None, Query()] = None):
    # todo переделать MenuUpdateTime
    # menu_update = db.query(MenuUpdateTime).one_or_none()
    # latest_update = menu_update.time if menu_update else None
    # if latest_update == time:
    #     return None
    return {
        "coffee_house_name": coffee_house.name,
        "time": datetime.now(),
        "products": await coffee_house_products(coffee_house, db),
        "toppings": await coffee_house_toppings(coffee_house, db),
    }


@router.get('/menu',
            tags=['common', 'menu'],
            description="Возвращает меню всех кофеен",
            response_model=list[CoffeeHouseMenuResponse])
async def menu(
        db: Annotated[Session, Depends(get_db)]):
    result = []
    for coffee_house in db.query(CoffeeHouse).all():
        result.append(await coffee_house_menu(coffee_house, db))
    return result


@router.get('/coffee_houses',
            tags=['common', 'menu'],
            description='Возвращает список кофеен с именем и расположением',
            response_model=list[CoffeeHouseResponse])
async def get_coffeehouses(db: Session = Depends(get_db)):
    result = []
    for house in db.query(CoffeeHouse).all():
        house_data = {
            "coffee_house_name": house.name,
            "branches": []
        }
        for branch in house.branches:
            branch_data = branch.data('chat_id', 'is_active', 'coffee_house_name')

            today_worktime = coffee_house_branch_worktime_today(branch, db)
            branch_data.update(today_worktime.dict())

            house_data['branches'].append(branch_data)
        result.append(house_data)
    return result
