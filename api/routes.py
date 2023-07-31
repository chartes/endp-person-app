"""
routes.py

Api endpoints.
"""
from typing import List
from fastapi import (APIRouter,
                     Depends)
from fastapi_pagination import (Page, paginate)
from fastapi_pagination.utils import disable_installed_extensions_check
disable_installed_extensions_check()

from sqlalchemy.orm import Session

from .database import get_db
from .crud import get_persons, get_event_by_person_id
from .schemas import PersonOut, EventScheme

api_router = APIRouter()


@api_router.get("/", tags=["root"])
async def read_root():
    return {"message": "Welcome to e-NDP API"}


@api_router.get("/persons/{person_id}", tags=["persons"])
async def read_person(person_id: int):
    return {
        "person_id": person_id,
    }


@api_router.get("/persons/", response_model=Page[PersonOut], tags=["persons"])
async def read_persons(db: Session = Depends(get_db)):
    return paginate(get_persons(db))
