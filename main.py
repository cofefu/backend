from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bot import bot_api
from bot.bot_api import set_webhook
from urls import api

tags_metadata = [
    {
        "name": "common",
        "description": "Для получения общей информации из бд",
    }
]

app = FastAPI(
    openapi_tags=tags_metadata,
    docs_url='/api/docs',
    redoc_url='/api/redoc'
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
