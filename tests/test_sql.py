"""
Tests for SQL CRUD operations on DB model.
"""
import pytest
from sqlalchemy.exc import IntegrityError

from tests.conftest import local_session
from api.models import (User,
                        Person,
                        Event,
                        PersonHasKbLinks,
                        PersonHasFamilyRelationshipType,
                        PlacesTerm,
                        ThesaurusTerm)

# -- USER --


def test_read_user():
    """read an existing user"""
    with local_session as session:
        user = session.query(User).first()
        assert user is not None
        assert user.username == "admin"


def test_read_unknown_user():
    """read an unknown user"""
    with local_session as session:
        user = session.query(User).filter(User.username == "user1").first()
        assert user is None


def test_create_user():
    """create a new user"""
    with local_session as session:
        user = User()
        user.username = "user1"
        user.email = "user1@chartes.com"
        user.set_password("user1")
        session.add(user)
        session.commit()
        user = session.query(User).filter(User.username == "user1").first()
        assert user is not None
        assert user.username == "user1"

# -- PERSON --


def test_read_an_existing_person():
    """read an existing person"""
    with local_session as session:
        person = session.query(Person).first()
        assert person is not None
        assert person.pref_label == "Jean d’Acy"
        assert person.is_canon is False
        person = session.query(Person).filter(Person.pref_label == "Jean d’Acy").first()
        assert person is not None
        assert person.pref_label == "Jean d’Acy"
        assert person.is_canon is False

