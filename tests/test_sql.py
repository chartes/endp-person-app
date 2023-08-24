"""
Tests for CRUD operations on DB model.
"""

from tests.conftest import local_session
from api.models import (User,
                        Person,
                        Event,
                        PersonHasKbLinks,
                        PersonHasFamilyRelationshipType)


def test_read_user():
    """read an existing user"""
    user = local_session.query(User).first()
    assert user is not None
    assert user.username == "admin"


def test_read_unknown_user():
    """read an unknown user"""
    user = local_session.query(User).filter(User.username == "user1").first()
    assert user is None


def test_create_user():
    """create a new user"""
    user = User()
    user.username = "user1"
    user.email = "user1@chartes.com"
    user.set_password("user1")
    local_session.add(user)
    local_session.commit()
    user = local_session.query(User).filter(User.username == "user1").first()
    assert user is not None
    assert user.username == "user1"

# -- PERSON --


def test_read_an_existing_person():
    """read an existing person"""
    person = local_session.query(Person).first()
    assert person is not None
    assert person.pref_label == "Jean d’Acy"
    assert person.is_canon is False
    person = local_session.query(Person).filter(Person.pref_label == "Jean d’Acy").first()
    assert person is not None
    assert person.pref_label == "Jean d’Acy"
    assert person.is_canon is False


def test_read_an_unknown_person():
    """read an unknown person"""
    person = local_session.query(Person).filter(Person.pref_label == "Foo bar").first()
    assert person is None


def test_update_an_existing_person():
    """update an existing person"""
    person = local_session.query(Person).first()
    assert person is not None
    assert person.pref_label == "Jean d’Acy"
    assert person.is_canon is False
    person.pref_label = "Jean d’Acy (test)"
    person.is_canon = True
    local_session.commit()
    person = local_session.query(Person).filter(Person.pref_label == "Jean d’Acy (test)").first()
    person_remove = local_session.query(Person).filter(Person.pref_label == "Jean d’Acy").first()
    assert person is not None
    assert person.pref_label == "Jean d’Acy (test)"
    assert person.is_canon is True
    assert person_remove is None

def test_update_delete_retrieve_person():
    """update an existing person"""
    person = local_session.query(Person).first()
    # create fake kb links for this person
    kb_links = [
        PersonHasKbLinks(
        person_id=person.id,
        type_kb="Wikidata",
        url="https://www.wikidata.org/wiki/Q90"
    ), PersonHasKbLinks(
        person_id=person.id,
        type_kb="Collecta",
        url="https://www.collecta.fr/16"
    ), PersonHasKbLinks(
        person_id=person.id,
        type_kb="Collecta",
        url="https://www.collecta.fr/18"
    ), PersonHasKbLinks(
        person_id=person.id,
        type_kb="Studium Parisiense",
        url="https://www.studium-parisiense.fr/40"
    )]
    local_session.add_all(kb_links)
    local_session.commit()
    # test if kb links are created
    kb_links = local_session.query(PersonHasKbLinks).filter(PersonHasKbLinks.person_id == person.id).all()
    assert len(kb_links) == 4
    assert kb_links[0].type_kb == "Wikidata"
    assert kb_links[0].id == 88
    assert kb_links[1].type_kb == "Collecta"
    assert kb_links[1].id == 89
    # create fake family relations for this person
    family_relations = [
        PersonHasFamilyRelationshipType(
        person_id=person.id,
        relative_id=59,
        relation_type="fils de"),
        PersonHasFamilyRelationshipType(
            person_id=person.id,
            relative_id=35,
            relation_type="père de")
        ]
    local_session.add_all(family_relations)
    local_session.commit()
    # test if family relations are created
    family_relations = local_session.query(PersonHasFamilyRelationshipType).filter(PersonHasFamilyRelationshipType.person_id == person.id).all()
    assert len(family_relations) == 2
    assert family_relations[0].relation_type == "père de"
    assert family_relations[0].id == 66
    person_relative = local_session.query(Person).filter(Person.id == family_relations[0].relative_id).first()
    assert person_relative.pref_label == "Geoffroy d’Avallon"
    # create fake events for this person
    events = [
        Event(
            type="Entrée",
            person_id=person.id,
            date="1423-03",
            image_url="https://www.nakala-fake/1",
            place_term_id=225,
            person_thesaurus_term_id=142,
            predecessor_id=100,
            comment="test"
        ),
        Event(
            type="Sortie",
            person_id=person.id,
            predecessor_id=75,
            person_thesaurus_term_id=311,
        )
    ]
    for event in events:
        Event.before_insert_create_id_ref(event, local_session, Event)
        local_session.add(event)
        local_session.commit()
    # test if events are created
    events = local_session.query(Event).filter(Event.person_id == person.id).all()
    assert len(events) == 3
    assert events[0].type == "Entrée"
    assert events[0].id == 1150
    assert events[0]._id_endp == "event_1150"




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

