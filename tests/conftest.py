from typing import Generator

import pytest
from starlette.testclient import TestClient

from db import SessionLocal
from fastapiProject.main import app


@pytest.fixture(scope="session")
def db() -> Generator:
    yield SessionLocal()


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c
