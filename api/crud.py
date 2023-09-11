"""
crud.py

CRUD operations.
Reusable functions to interact with the data in the database.
"""

from typing import (Union,
                    Type)

from sqlalchemy import Row
from sqlalchemy.orm import Session
from sqlalchemy.sql._typing import _TP

from .models import (Person,
                     User,
                     ThesaurusTerm,
                     PlacesTerm)


def get_user(db: Session, args: dict) \
        -> Union[User, None]:
    """Get a user from the database."""
    return db.query(User).filter_by(**args).first()


def get_person(db: Session, args: dict) \
        -> Union[Person, None]:
    """Get a person from the database."""
    return db.query(Person).filter_by(**args).first()


def get_persons(db: Session) \
        -> Union[list[Type[Person]], None]:
    """Get all the persons from the database."""
    return db.query(Person).all()


def get_thesaurus_term(db: Session, model: str, args: dict) \
        -> Union[ThesaurusTerm, PlacesTerm, None]:
    """Get a term from the thesaurus filter by the endp id."""
    if model == "places":
        model_class = PlacesTerm
    elif model == "persons_terms":
        model_class = ThesaurusTerm
    else:
        return None
    return db.query(model_class).filter_by(**args).first()


def get_thesaurus_terms(db: Session, model: str, condition: str = 'topic') \
        -> list[Row[_TP]]:
    """Get all the terms from the thesaurus order with a condition."""
    model_classes = {
        "places": PlacesTerm,
        "persons_terms": ThesaurusTerm
    }
    return db.query(model_classes[model]).order_by(condition).all()


def get_events(db: Session,  args: dict) \
        -> Union[dict, None]:
    """Get all the events from a person."""
    person = db.query(Person).filter_by(**args).first()
    if person is None:
        return None
    return {'_id_endp': person._id_endp,
            'pref_label': person.pref_label,
            'events': [{
                '_id_endp': event._id_endp,
                'date': event.date,
                'image_url': event.image_url,
                'place_term': event.place_term,
                'thesaurus_term_person': event.thesaurus_term_person,
                'predecessor': {
                    '_id_endp': event.predecessor._id_endp,
                    'pref_label': event.predecessor.pref_label
                } if event.predecessor else None,
            } for event in person.events]}

