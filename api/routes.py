"""
routes.py

Api endpoints.
"""
from typing import List
from fastapi import (APIRouter,
                     Depends)

from sqlalchemy.orm import Session

from .database import get_db
from .crud import get_persons, get_event_by_person_id
from .schemas import PersonScheme, EventScheme

api_router = APIRouter()


@api_router.get("/", tags=["root"])
async def read_root():
    return {"message": "Welcome to e-NDP API"}


@api_router.get("/persons/{person_id}", tags=["persons"])
async def read_person(person_id: int):
    return {
        "person_id": person_id,
    }


@api_router.get("/persons/", response_model=List[PersonScheme], tags=["persons"])
def read_persons(db: Session = Depends(get_db)):
    persons = [PersonScheme(
        id=p.id,
        pref_label=p.pref_label,
        id_endp=p._id_endp,
        events=[EventScheme(id=e.id, type=e.type, date=e.date) for e in get_event_by_person_id(db, p.id)]
    )
     for p in get_persons(db)]
    return persons
