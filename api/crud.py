"""
crud.py

CRUD operations.
Reusable functions to interact with the data in the database.
"""

from typing import List
from sqlalchemy.orm import Session

from .models import (Person,
                     Event,
                     User)

# User #


def get_user(db: Session, args: dict):
    return db.query(User).filter_by(**args).first()


# Person #


def get_person(db: Session, args: dict):
    return db.query(Person).filter_by(**args).first()


def get_persons(db: Session):
    return db.query(Person).all()

# ThesaurusTerm #


def get_thesaurus_term(db: Session, model, args: dict):
    return db.query(model).filter_by(**args).first()


def get_thesaurus_terms(db: Session, model, condition: dict):
    return db.query(model).order_by(condition).all()

# Events #


def get_event_by_person_id(db: Session, person_id: int):
    return db.query(Event).filter(Event.person_id == person_id).all()

