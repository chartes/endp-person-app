"""
Tests for the SQL tables.
"""

from api.models import User, Person


def test_item(db_session, ):
    print("here")
    obj_out = db_session.query(User).first()
    assert obj_out.username == "admin"


def test_person(db_session, ):
    obj_out = db_session.query(Person).first()
    assert obj_out.pref_label == "Jean d’Acy"


# add all tests here
# SUPPRESSION
# - tester si une personne est supprimé on supprime toutes les relations associés (events, links, familiy relations, etc.)
# - si un terme personne ou un lieu est supprimé on supprime toutes les relations associés (events)

# CREATION
# - si un item est ajouté vérifier qu'on s'on identifiant forgé s'incrémente bien

