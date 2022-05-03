from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bot import bot_api
from bot.bot_api import set_webhook
from bot.filters import bind_bot_filters
from app import api

from fastapiProject.settings import API_PREFIX

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

app.include_router(api.router, prefix='/api')
app.include_router(bot_api.router, prefix='/bot')


@app.on_event("startup")
async def on_startup():
    set_webhook()
    bind_bot_filters()
