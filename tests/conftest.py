"""conftest.py

File that pytest automatically looks for in any directory.
"""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from api.database import (BASE, get_db)
from api.main import (app)
from api.models import User
from api.database_utils import populate_db_process


SQLALCHEMY_DATABASE_TEST_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=True,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

BASE.metadata.create_all(bind=engine)


def override_get_db():
    """Override the get_db() dependency with a test database."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

local_session = TestingSessionLocal()
# populate database from last migration
# 1) add default user
User.add_default_user(in_session=local_session)
# 2) add data
populate_db_process(in_session=local_session)

client = TestClient(app)
