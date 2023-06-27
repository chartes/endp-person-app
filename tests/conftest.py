"""
conftest.py

File that pytest automatically looks for in any directory.
"""

import sys
import os
from typing import (Any,
                    Generator)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.database import BASE, get_db
from api.models import User
from api.main import create_app
from api.database_utils import populate_db_process
from api.config import BASE_DIR, settings


def start_application():
    return create_app()


SQLALCHEMY_DATABASE_URI = f"sqlite:////{os.path.join(BASE_DIR, 'db/endp.test.sqlite')}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def app() -> Generator[FastAPI, Any, None]:
    """
    Create a new instance of the app and fresh app.
    """
    # Use here the same database as the application (from script sh)
    # BASE.metadata.create_all(bind=engine)
    _app = start_application()
    yield _app
    # BASE.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(app: FastAPI) -> Generator[SessionTesting, Any, None]:
    """
    Create a new instance of the app and fresh app.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionTesting(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(app: FastAPI, db_session: SessionTesting) -> Generator[TestClient, Any, None]:
    """
    Create a new FastAPI TestClient that uses the `db_session` fixture to override
    the `get_db` dependency that is injected into routes.
    """

    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    User.add_default_user()
    populate_db_process()
    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as client:
        yield client
