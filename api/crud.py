"""
crud.py

CRUD operations.
Reusable functions to interact with the data in the database.
"""

from typing import (Union,
                    List,
                    Type)

from sqlalchemy import (Row,
                        func,
                        distinct)
from sqlalchemy.orm import Session
from sqlalchemy.sql._typing import _TP

from .models import (Person,
                     Event,
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


def get_persons(db: Session, only_canon: bool = False):
    """Get all the persons from the database.
    If only_canon is True, only the canon persons are returned."""
    return db.query(Person).filter_by(is_canon=True).all() if only_canon else db.query(Person).all()


def get_thesaurus_term(db: Session, model: str, args: dict) \
        -> Union[ThesaurusTerm, PlacesTerm, None]:
    """Get a term from the thesaurus filter by the endp id."""
    model_classes = {
        "places": PlacesTerm,
        "persons_terms": ThesaurusTerm
    }
    return db.query(
        model_classes[model]
        if isinstance(model, str)
        else model).filter_by(**args).first()

def get_thesaurus_terms(
    db: Session,
    model: Union[Type[ThesaurusTerm], Type[PlacesTerm], str],
    place_endp_ids: List[str] = [],
    person_term_endp_ids: List[str] = [],
    condition: str = "topic",
):
    """
    By Default, without filters: returns all terms (from the requested model) actually used by at least one Event.
    With filters: keeps people who have
    *all* selected places AND *all* selected person terms
        (AND inter- and intra-category, not necessarily on the same event),
      then returns the terms (from the requested model) present in *their* events.
    NB: Terms already selected are not removed here (managed on the front end).
    """
    model_classes = {
        "places": PlacesTerm,
        "persons_terms": ThesaurusTerm,
    }
    resolved_model = model_classes[model] if isinstance(model, str) else model
    order_col = getattr(resolved_model, condition)

    # Without filter pass
    if not place_endp_ids and not person_term_endp_ids:
        if resolved_model is PlacesTerm:
            return (
                db.query(PlacesTerm)
                .join(Event, Event.place_term_id == PlacesTerm.id)
                .filter(Event.place_term_id.isnot(None))
                .distinct()
                .order_by(order_col)
                .all()
            )
        else:
            return (
                db.query(ThesaurusTerm)
                .join(Event, Event.person_thesaurus_term_id == ThesaurusTerm.id)
                .filter(Event.person_thesaurus_term_id.isnot(None))
                .distinct()
                .order_by(order_col)
                .all()
            )

    # --- 2) AND opt ---
    place_ok_ids = None
    term_ok_ids = None

    if place_endp_ids:
        place_ok_ids = {
            pid
            for (pid,) in (
                db.query(Event.person_id)
                .join(PlacesTerm, PlacesTerm.id == Event.place_term_id)
                .filter(PlacesTerm._id_endp.in_(place_endp_ids))
                .group_by(Event.person_id)
                .having(
                    func.count(distinct(PlacesTerm._id_endp))
                    >= len(set(place_endp_ids))
                )
                .all()
            )
        }

    if person_term_endp_ids:
        term_ok_ids = {
            pid
            for (pid,) in (
                db.query(Event.person_id)
                .join(ThesaurusTerm, ThesaurusTerm.id == Event.person_thesaurus_term_id)
                .filter(ThesaurusTerm._id_endp.in_(person_term_endp_ids))
                .group_by(Event.person_id)
                .having(
                    func.count(distinct(ThesaurusTerm._id_endp))
                    >= len(set(person_term_endp_ids))
                )
                .all()
            )
        }

    if place_ok_ids is not None and term_ok_ids is not None:
        matching_person_ids = place_ok_ids & term_ok_ids
    else:
        matching_person_ids = place_ok_ids or term_ok_ids or set()

    if not matching_person_ids:
        return []

    if resolved_model is PlacesTerm:
        term_ids = [
            tid
            for (tid,) in (
                db.query(distinct(Event.place_term_id))
                .filter(
                    Event.person_id.in_(matching_person_ids),
                    Event.place_term_id.isnot(None),
                )
                .all()
            )
            if tid is not None
        ]
        if not term_ids:
            return []
        return (
            db.query(PlacesTerm)
            .filter(PlacesTerm.id.in_(term_ids))
            .order_by(order_col)
            .all()
        )

    else:
        term_ids = [
            tid
            for (tid,) in (
                db.query(distinct(Event.person_thesaurus_term_id))
                .filter(
                    Event.person_id.in_(matching_person_ids),
                    Event.person_thesaurus_term_id.isnot(None),
                )
                .all()
            )
            if tid is not None
        ]
        if not term_ids:
            return []
        return (
            db.query(ThesaurusTerm)
            .filter(ThesaurusTerm.id.in_(term_ids))
            .order_by(order_col)
            .all()
        )

def get_events(db: Session, args: dict) \
        -> Union[dict, None]:
    """Get all the events from a person."""
    person = db.query(Person).filter_by(**args).first()
    if person is None:
        return None
    return {'_id_endp': person._id_endp,
            'pref_label': person.pref_label,
            'events': [{
                '_id_endp': event._id_endp,
                'type': event.type,
                'date': event.date,
                'image_url': event.image_url,
                'place_term': event.place_term,
                'thesaurus_term_person': event.thesaurus_term_person,
                'comment': event.comment,
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
