"""conftest.py

File that pytest automatically looks for in any directory.
"""
import os

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from api.database import (BASE, get_db)
from api.main import (app)
from api.models import User
from api.database_utils import populate_db_process
from api.config import BASE_DIR, settings

# in local uncomment (in memory)
# SQLALCHEMY_DATABASE_TEST_URL = "sqlite://"
# on CI Actions
SQLALCHEMY_DATABASE_TEST_URL = f"sqlite:///{os.path.join(BASE_DIR, 'db/endp.test.sqlite')}"

engine = create_engine(
    SQLALCHEMY_DATABASE_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    #echo=True,
    #pool_size=20,
    #max_overflow=0,
    #pool_timeout=300,
    #pool_recycle=3600,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

BASE.metadata.drop_all(bind=engine)
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
