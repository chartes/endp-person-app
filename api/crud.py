"""
crud.py

CRUD operations.
Reusable functions to interact with the data in the database.
"""

from typing import List
from sqlalchemy.orm import Session

from .models import Person, Event


def get_persons(db: Session):
    return db.query(Person).all()


def get_event_by_person_id(db: Session, person_id: int):
    return db.query(Event).filter(Event.person_id == person_id).all()

