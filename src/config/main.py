import importlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import settings

tags_metadata = [
    {
        'name': 'common',
        'description': 'Для получения общей информации из бд',
    },
    {
        'name': 'jwt require',
        'description': 'Требуется jwt-токен'
    },
    {
        'name': 'menu',
        'description': 'Для получения информации о меню'
    },
    {
        'name': 'orders',
        'description': 'Для взаимодействия с заказами (создание, отмена и т.д.)'
    },
    {
        'name': 'auth',
        'description': 'Все связанное с пользователем'
    }
]

app = FastAPI(
    openapi_tags=tags_metadata,
    docs_url='/api/docs',
    redoc_url='/api/redoc',
    root_path=settings.api_prefix,
    openapi_url='/api/openapi.json',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT'],
    allow_headers=['*'],
)

for app_ in settings.apps:
    router = getattr(importlib.import_module(f'src.{app_}.urls'), 'router')
    if router is None:
        raise ImportError(f'The {app_} application does not contain "router"')
    app.include_router(router)
