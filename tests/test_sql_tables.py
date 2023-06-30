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

# USERS tests
# - tester l'ajout d'un utilisateur
# - tester la modification sur une personne par un utilisateur prise en compte du last editor


# Data
# - tester l'ajout d'un item (person, thesaurus places et person term)
# - tester la suppression d'un item (person, thesaurus places et person term)
# - tester si un item evenement est supprimé
# - tester si un item evenement est modifié
# - tester si un thesaurus term est supprimé, suppression en cascade des relations aux events
# - tester si un thesaurus term est modifié, modification en cascade des relations aux events


# SUPPRESSION
# - tester si une personne est supprimé on supprime toutes les relations associés (events, links, familiy relations, etc.)
# - si un terme personne ou un lieu est supprimé on supprime toutes les relations associés (events)

# CREATION
# - si un item est ajouté vérifier qu'on s'on identifiant forgé s'incrémente bien

