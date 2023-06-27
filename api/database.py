"""
database.py

Database connection and session management.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (sessionmaker,
                            scoped_session)

from .config import BASE_DIR, settings

SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, settings.DB_URI)}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    # needed for sqlite
    connect_args={'check_same_thread': False},
    # pool_size=20,
    # max_overflow=0,
    # pool_timeout=300,
    # pool_recycle=3600
)

session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
BASE = declarative_base()


# Dependency for FastAPI endpoints
# to get a database connection.
def get_db() -> scoped_session:
    """
    Get a database connection.
    :return: scoped_session
    :rtype: scoped_session
    """
    db = session
    try:
        yield db
    finally:
        db.close()
