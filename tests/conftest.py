"""conftest.py

File that pytest automatically looks for in any directory.
"""
import os

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from api.database import (BASE, get_db)
from api.index_conf import ix
from api.main import (app)
from api.models import User
from api.database_utils import populate_db_process
from api.config import BASE_DIR
from api.index_fts.index_utils import (create_index,
                                       populate_index)

WHOOSH_INDEX_DIR = os.path.join(BASE_DIR, "index_endp")
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
# 3) create index
create_index(index_dir=WHOOSH_INDEX_DIR)
# 4) populate index
populate_index(session=local_session, index_=ix)

client = TestClient(app)
