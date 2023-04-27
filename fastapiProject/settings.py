import pathlib
from functools import lru_cache

from pydantic import BaseSettings, PostgresDsn, validator
from datetime import timedelta
from pathlib import Path


@lru_cache
class Settings(BaseSettings):
    base_dir: pathlib.WindowsPath = Path(__file__).resolve().parent.parent
    apps: tuple[str, ...] = ('app', 'bot')

    db_engine: str = 'postgresql'
    db_user: str = 'postgres'
    db_password: str
    db_host: str = 'localhost'
    db_port: int = 5432
    db_name: str
    database_url: PostgresDsn = None
    test_database_url: PostgresDsn = None

    @validator("database_url")
    def assemble_db_connection(cls, v: str | None, values: dict) -> str:
        if isinstance(v, str):
            return v
        # "scheme://user:password@host:port/path"
        return PostgresDsn.build(
            scheme=values.get('db_engine'),
            user=values.get('db_user'),
            password=values.get('db_password'),
            host=values.get('db_host'),
            port=str(values.get('db_port')),
            path=f"/{values.get('db_name')}"
        )

    allow_origins: list[str, ...] | str = ['*']

    @validator('allow_origins')
    def setup_allow_origins(cls, v: list[str, ...] | str):
        if isinstance(v, list):
            return v
        return list(v.split(','))

    server_host: str = '127.0.0.1'
    server_port: int = 8000

    bot_token: str
    bot_port: int = 443
    bot_prefix: str = ''
    feedback_chat: str
    domain: str

    jwt_secret_key: str
    jwt_algorithm: str = 'HS256'

    workers: int = 1
    api_prefix: str = ''

    max_not_picked_orders: int = 2
    max_product_in_order: int = 5
    order_timeout: timedelta = timedelta()
    time_to_cancel_order = timedelta()

    sbis_app_client_id: str | None
    sbis_app_secret: str | None
    sbis_secret_key: str | None

    class Config:
        env_file = './.env'


settings = Settings()
