import importlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapiProject.settings import API_PREFIX, APPS

tags_metadata = [
    {
        "name": "common",
        "description": "Для получения общей информации из бд",
    },
    {
        "name": 'jwt require',
        'description': 'Требуется jwt-токен'
    }
]

app = FastAPI(
    openapi_tags=tags_metadata,
    docs_url='/api/docs',
    redoc_url='/api/redoc',
    openapi_prefix=API_PREFIX,
    openapi_url='/api/openapi.json',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for app_ in APPS:
    a = importlib.import_module('%s.urls' % app_)
    router = getattr(a, 'router')
    if router is None:
        raise ImportError(f'The {app_} application does not contain "router"')
    app.include_router(router)
