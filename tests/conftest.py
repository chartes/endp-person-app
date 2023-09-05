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
from api.models import User, Person
from api.database_utils import populate_db_process
from api.config import BASE_DIR, settings
from api.index_fts.index_utils import (create_index,
                                       create_store,
                                       populate_index)
from api.index_conf import st
from api.index_fts.schemas import PersonIdxSchema

# set up ENV var for testing
os.environ["ENV"] = "test"

WHOOSH_INDEX_DIR = os.path.join(BASE_DIR, settings.WHOOSH_INDEX_DIR)
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
create_store(st, WHOOSH_INDEX_DIR)
create_index(st, PersonIdxSchema)
# add default user
User.add_default_user(in_session=local_session)
# add data
populate_db_process(in_session=local_session)
# populate index
# populate_index(session=local_session, index_=ix, model=Person)

client = TestClient(app)
