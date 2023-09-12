"""
crud.py

CRUD operations.
Reusable functions to interact with the data in the database.
"""

from typing import (Union,
                    List)

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
        -> list:
    """Get all the persons from the database."""
    return db.query(Person).all()


def get_thesaurus_term(db: Session, model: str, args: dict) \
        -> Union[ThesaurusTerm, PlacesTerm, None]:
    """Get a term from the thesaurus filter by the endp id."""
    model_classes = {
        "places": PlacesTerm,
        "persons_terms": ThesaurusTerm
    }
    return db.query(model_classes[model]).filter_by(**args).first()


def get_thesaurus_terms(db: Session, model: str, condition: str = 'topic') \
        -> List[Row[_TP]]:
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


def get_family_relatives(db: Session, args: dict) \
        -> Union[dict, None]:
    """Get all the family relationships from a person."""
    person = db.query(Person).filter_by(**args).first()
    if person is None:
        return None
    return {'_id_endp': person._id_endp,
            'pref_label': person.pref_label,
            'relatives': [{
                '_id_endp': relative._id_endp,
                'relation_type': relative.relation_type,
                'relative': {
                    '_id_endp': relative.relative._id_endp,
                    'pref_label': relative.relative.pref_label
                } if relative.relative else None,
            } for relative in person.family_links]}
