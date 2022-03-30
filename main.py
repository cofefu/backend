from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bot import bot_api
from bot.bot_api import set_webhook
from urls import api

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router)
app.include_router(bot_api.router)


# api
# bot_api
# fastapp_funcs / events


@app.on_event("startup")
async def on_startup():
    set_webhook()
