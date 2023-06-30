import json
from datetime import timedelta
from typing import Generator

import pytest
from pydantic import AnyHttpUrl
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.testclient import TestClient
from telebot import apihelper, util

from app.dependencies import get_db
from fastapiProject.main import app
from fastapiProject.settings import settings


@pytest.fixture(scope="session")
def db() -> Generator:
    engine = create_engine(settings.test_database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield SessionLocal()


async def test_db() -> Session:
    engine = create_engine(settings.test_database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c


def custom_sender(method, url: str, **kwargs):
    if url.endswith('getWebhookInfo'):
        webhook_url = AnyHttpUrl.build(
            scheme='https',
            host=settings.bot_domain,
            port=str(settings.bot_port),
            path=f"/{settings.bot_prefix}/bot/{settings.bot_token.replace(':', '_')}/"
        )
        result = {
            'url': webhook_url,
            'has_custom_certificate': False,
            'pending_update_count': 0,
        }
        return util.CustomRequestResponse(json.dumps({'ok': True, 'result': result}))

    return util.CustomRequestResponse(
        '{"ok":true,"result":{"message_id": 1, "date": 1, "chat": {"id": 1, "type": "private"}}}')


settings.time_to_cancel_order = timedelta()
app.dependency_overrides[get_db] = test_db
apihelper.CUSTOM_REQUEST_SENDER = custom_sender
