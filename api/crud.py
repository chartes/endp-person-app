"""
crud.py

CRUD operations.
Reusable functions to interact with the data in the database.
"""

from typing import (Union,
                    List)
from collections import defaultdict

from sqlalchemy import Row, or_, and_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql._typing import _TP
from sqlalchemy import func, select
from sqlalchemy.orm import aliased

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


def get_persons_filtered_by_events(
    db: Session,
    only_canon: bool = False,
    place_terms: List[str] = None,
    thesaurus_terms_person: List[str] = None,
    combine_filters_with_or: bool = False
) -> List[Person]:
    """
    Optimized filter persons based on place_terms and thesaurus_terms_person using subqueries.
    """
    # Step 1: Build filters for events
    filters = []

    if place_terms:
        place_subquery = select(PlacesTerm.id).filter(PlacesTerm.term_fr.in_(place_terms))
        filters.append(Event.place_term_id.in_(place_subquery))


    if thesaurus_terms_person:
        thesaurus_subquery = select(ThesaurusTerm.id).filter(ThesaurusTerm.term_fr.in_(thesaurus_terms_person))
        filters.append(Event.person_thesaurus_term_id.in_(thesaurus_subquery))

    # Combine filters using "or" or "and"
    if filters:
        combined_filter = or_(*filters) if combine_filters_with_or else and_(*filters)
        event_subquery = select(Event.person_id).filter(combined_filter).distinct()
    else:
        event_subquery = select(Event.person_id).distinct()

    # Step 2: Query persons based on the event subquery
    person_query = db.query(Person).filter(Person.id.in_(event_subquery))

    if only_canon:
        person_query = person_query.filter(Person.is_canon == True)

    return person_query.all()


def get_freq_terms_from_persons(db: Session, person_ids: List[int]) -> dict:
    """
    Retrieve the frequency of thesaurus terms (places and persons) linked to a list of person IDs.
    Output: Structured JSON grouped by type (places/persons) and topic, sorted by occurrences.
    """
    # Subquery for thesaurus terms (persons)
    person_term_count_subquery = (
        db.query(
            Event.person_thesaurus_term_id.label("term_id"),
            func.count(Event.person_id).label("term_count")
        )
        .filter(Event.person_id.in_(person_ids))
        .group_by(Event.person_thesaurus_term_id)
        .subquery()
    )

    # Subquery for place terms
    place_term_count_subquery = (
        db.query(
            Event.place_term_id.label("term_id"),
            func.count(Event.person_id).label("term_count")
        )
        .filter(Event.person_id.in_(person_ids))
        .group_by(Event.place_term_id)
        .subquery()
    )

    # Aliases for thesaurus terms and place terms
    PersonTermAlias = aliased(ThesaurusTerm)
    PlaceTermAlias = aliased(PlacesTerm)

    # Query for thesaurus terms (persons)
    person_terms_query = (
        db.query(
            PersonTermAlias.id,
            PersonTermAlias._id_endp,
            PersonTermAlias.topic,
            PersonTermAlias.term_fr,
            PersonTermAlias.term,
            person_term_count_subquery.c.term_count
        )
        .join(person_term_count_subquery, PersonTermAlias.id == person_term_count_subquery.c.term_id)
    )

    # Query for place terms
    place_terms_query = (
        db.query(
            PlaceTermAlias.id,
            PlaceTermAlias._id_endp,
            PlaceTermAlias.topic,
            PlaceTermAlias.term_fr,
            PlaceTermAlias.term,
            place_term_count_subquery.c.term_count
        )
        .join(place_term_count_subquery, PlaceTermAlias.id == place_term_count_subquery.c.term_id)
    )

    # Execute queries
    person_terms = person_terms_query.all()
    place_terms = place_terms_query.all()

    # Structure the response
    structured_response = {
        "persons_terms": defaultdict(list),
        "places_terms": defaultdict(list),
    }

    # Group thesaurus terms by topic and sort by count
    for term in person_terms:
        structured_response["persons_terms"][term.topic].append({
            "id": term.id,
            "id_endp": term._id_endp,
            "term_fr": term.term_fr,
            "term": term.term,
            "count": term.term_count,
        })

    # Group place terms by topic and sort by count
    for term in place_terms:
        structured_response["places_terms"][term.topic].append({
            "id": term.id,
            "id_endp": term._id_endp,
            "term_fr": term.term_fr,
            "term": term.term,
            "count": term.term_count,
        })

    # Sort each topic group by count (descending order)
    structured_response["persons_terms"] = {
        topic: sorted(terms, key=lambda x: x["count"], reverse=True)
        for topic, terms in structured_response["persons_terms"].items()
    }
    structured_response["places_terms"] = {
        topic: sorted(terms, key=lambda x: x["count"], reverse=True)
        for topic, terms in structured_response["places_terms"].items()
    }

    return structured_response

def get_persons(db: Session, only_canon: bool = False):
    """Get all the persons from the database.
    If only_canon is True, only the canon persons are returned."""
    #res = db.query(Person).filter_by(is_canon=True).all() if only_canon else db.query(Person).all()
    persons_endp_ids = ['person_endp_PYve6qzO',

                        'person_endp_KYu4gG1H']
    # find the persons with the endp id
    res = db.query(Person).filter(Person._id_endp.in_(persons_endp_ids)).all()
    print(get_freq_terms_from_persons(db, [p.id for p in res]))
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


def get_thesaurus_terms(db: Session, model: str, condition: str = 'topic') \
        -> List[Row[_TP]]:
    """Get all the terms from the thesaurus order with a condition."""
    model_classes = {
        "places": PlacesTerm,
        "persons_terms": ThesaurusTerm
    }
    return db.query(
        model_classes[model]
        if isinstance(model, str)
        else model).order_by(condition).all()


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