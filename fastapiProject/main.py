import importlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapiProject.settings import settings

tags_metadata = [
    {
        'name': 'common',
        'description': 'Для получения общей информации из бд',
    },
    {
        'name': 'jwt require',
        'description': 'Требуется jwt-токен'
    }
]

app = FastAPI(
    openapi_tags=tags_metadata,
    docs_url='/api/docs',
    redoc_url='/api/redoc',
    openapi_prefix=settings.api_prefix,
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
    router = getattr(importlib.import_module(f'{app_}.urls'), 'router')
    if router is None:
        raise ImportError(f'The {app_} application does not contain "router"')
    app.include_router(router)
