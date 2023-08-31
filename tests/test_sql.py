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
    person = local_session.query(Person).filter(Person.id == 1).first()
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
    """update, delete and check data on existing person"""
    person = local_session.query(Person).first()
    person.pref_label = "Jean d’Acy"
    local_session.commit()
    person_id_endp = person._id_endp
    person_id = person.id
    # create fake data to update person
    data = [
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
        ),
        PersonHasFamilyRelationshipType(
            person_id=person.id,
            relative_id=59,
            relation_type="fils de"),
        PersonHasFamilyRelationshipType(
            person_id=person.id,
            relative_id=35,
            relation_type="père de"),
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
    local_session.add_all(data)
    local_session.commit()
    query_per = lambda model, per_id: local_session.query(model).filter(model.person_id == per_id).all()
    # retrieve ids of kb links
    kb_links_ids = [kb_link for kb_link in query_per(PersonHasKbLinks, person_id)]
    # retrieve ids of family relations
    family_relations_ids = [family_relation for family_relation in query_per(PersonHasFamilyRelationshipType, person_id)]
    # retrieve ids of events
    events_ids = [event for event in query_per(Event, person_id)]
    # delete person
    local_session.delete(person)
    local_session.commit()
    # check if person is deleted
    assert local_session.query(Person).filter(Person._id_endp == person_id_endp).first() is None
    # check if dependencies are deleted
    query_deps = lambda model, dep_id: local_session.query(model).filter(model.person_id == dep_id).first()
    for dependencies in [kb_links_ids, family_relations_ids, events_ids]:
        for dep in dependencies:
            if isinstance(dep, PersonHasKbLinks):
                assert query_deps(PersonHasKbLinks, dep.person_id) is None
            elif isinstance(dep, PersonHasFamilyRelationshipType):
                assert query_deps(PersonHasFamilyRelationshipType, dep.person_id) is None
            elif isinstance(dep, Event):
                assert query_deps(Event, dep.person_id) is None
    # check if relative person, place and thesaurus term are not deleted
    assert local_session.query(Person).filter(Person.id == 59).first() is not None
    assert local_session.query(Person).filter(Person.id == 35).first() is not None
    assert local_session.query(Person).filter(Person.id == 100).first() is not None
    assert local_session.query(Person).filter(Person.id == 75).first() is not None
    assert local_session.query(PlacesTerm).filter(PlacesTerm.id == 225).first() is not None
    assert local_session.query(ThesaurusTerm).filter(ThesaurusTerm.id == 142).first() is not None
    assert local_session.query(ThesaurusTerm).filter(ThesaurusTerm.id == 311).first() is not None


def test_remove_relative_person():
    """remove a relative person (test if events or family in relations are update)"""
    # if remove relative remove family relationships associated
    person = local_session.query(Person).filter(Person.id == 5).first()
    relative = local_session.query(Person).filter(Person.id == 587).first()
    family_relation = local_session.query(PersonHasFamilyRelationshipType).filter_by(person_id=person.id, relative_id=relative.id).first()
    assert family_relation is not None
    local_session.delete(relative)
    local_session.commit()
    assert local_session.query(Person).filter_by(id=person.id).first() is not None
    assert local_session.query(Person).filter_by(id=relative.id).first() is None
    assert local_session.query(PersonHasFamilyRelationshipType).filter_by(id=family_relation.id).first() is None
    # if remove predecessor in event don't remove event just update predecessor_id with null
    person1 = local_session.query(Person).filter(Person.id == 6).first()
    person2 = local_session.query(Person).filter(Person.id == 7).first()
    person3 = local_session.query(Person).filter(Person.id == 8).first()
    events1 = local_session.query(Event).filter_by(person_id=person1.id).all()
    events2 = local_session.query(Event).filter_by(person_id=person2.id).all()
    events3 = local_session.query(Event).filter_by(person_id=person3.id).all()
    assert len(events1) == 3
    assert len(events2) == 1
    assert len(events3) == 4
    new_events_id = []
    for per in [person1, person2, person3]:
        new_event = Event(
            type="Entrée",
            person_id=per.id,
            predecessor_id=10
        )
        local_session.add(new_event)
        local_session.commit()
        # retrieve endp id of new event
        new_event_id_endp = new_event._id_endp
        new_events_id.append((per.id, new_event_id_endp))
        # check if new event is added
        assert local_session.query(Event).filter_by(_id_endp=new_event_id_endp).first() is not None
    events1 = local_session.query(Event).filter_by(person_id=person1.id).all()
    events2 = local_session.query(Event).filter_by(person_id=person2.id).all()
    events3 = local_session.query(Event).filter_by(person_id=person3.id).all()
    assert len(events1) == 4
    assert len(events2) == 2
    assert len(events3) == 5
    # remove predecessor
    person = local_session.query(Person).filter(Person.id == 10).first()
    local_session.delete(person)
    local_session.commit()
    # check if person is deleted
    assert local_session.query(Person).filter(Person.id == 10).first() is None
    # check if events are updated
    for per_id, event_id in new_events_id:
        event = local_session.query(Event).filter_by(_id_endp=event_id).first()
        assert event is not None # event is not deleted
        assert event.predecessor_id is None # predecessor is updated


def test_remove_relative_term():
    """remove a relative term if events are update"""
    # if remove thesaurus term in event don't remove event just update term_id with null
    term = local_session.query(ThesaurusTerm).filter(ThesaurusTerm.id == 7).first()
    person_1 = local_session.query(Person).filter(Person.id == 674).first()
    person_2 = local_session.query(Person).filter(Person.id == 401).first()
    person_3 = local_session.query(Person).filter(Person.id == 448).first()
    assert term is not None
    assert person_1 is not None
    assert person_2 is not None
    assert person_3 is not None
    event1 = local_session.query(Event).filter_by(person_id=person_1.id, person_thesaurus_term_id=term.id).first()
    event2 = local_session.query(Event).filter_by(person_id=person_2.id, person_thesaurus_term_id=term.id).first()
    event3 = local_session.query(Event).filter_by(person_id=person_3.id, person_thesaurus_term_id=term.id).first()
    assert event1 is not None
    assert event2 is not None
    assert event3 is not None
    local_session.delete(term)
    local_session.commit()
    # check if term is deleted
    assert local_session.query(ThesaurusTerm).filter(ThesaurusTerm.id == 7).first() is None
    # check if events are updated
    event1 = local_session.query(Event).filter_by(person_id=person_1.id, person_thesaurus_term_id=term.id).first()
    event2 = local_session.query(Event).filter_by(person_id=person_2.id, person_thesaurus_term_id=term.id).first()
    event3 = local_session.query(Event).filter_by(person_id=person_3.id, person_thesaurus_term_id=term.id).first()
    assert event1 is None
    assert event2 is None
    assert event3 is None
    # check if persons are not deleted
    assert local_session.query(Person).filter(Person.id == 582).first() is not None
    assert local_session.query(Person).filter(Person.id == 401).first() is not None
    assert local_session.query(Person).filter(Person.id == 448).first() is not None
    # if remove place term in event don't remove event just update place_id with null
    event1 = local_session.query(Event).filter(Event.id == 3050).first()
    event2 = local_session.query(Event).filter(Event.id == 3051).first()
    event3 = local_session.query(Event).filter(Event.id == 3052).first()
    assert event1 is not None
    assert event2 is not None
    assert event3 is not None
    assert event1.place_term_id == 10
    assert event2.place_term_id == 10
    assert event3.place_term_id == 10
    # remove place term
    term = local_session.query(PlacesTerm).filter(PlacesTerm.id == 10).first()
    local_session.delete(term)
    local_session.commit()
    # check if term is deleted
    assert local_session.query(PlacesTerm).filter(PlacesTerm.id == 10).first() is None
    # check if events are updated
    event1 = local_session.query(Event).filter(Event.id == 3050).first()
    event2 = local_session.query(Event).filter(Event.id == 3051).first()
    event3 = local_session.query(Event).filter(Event.id == 3052).first()
    events = local_session.query(Event).filter_by(place_term_id=10).all()
    assert len(events) == 0
    assert event1 is None
    assert event2 is None
    assert event3 is None
    person_1 = local_session.query(Person).filter(Person.id == 269).first()
    person_2 = local_session.query(Person).filter(Person.id == 270).first()
    # check length of events
    events_1 = local_session.query(Event).filter_by(person_id=person_1.id).all()
    events_2 = local_session.query(Event).filter_by(person_id=person_2.id).all()
    for i, evt in enumerate(events_2, start=1):
        print(i, evt.id, evt.type, evt.place_term_id, evt.place_term, evt.person_thesaurus_term_id)
    assert len(events_1) == 10
    assert len(events_2) == 17
    place_term = local_session.query(PlacesTerm).filter(PlacesTerm.id == 177).first()
    assert place_term is not None
    local_session.delete(place_term)
    local_session.commit()
    # check if place term is deleted
    assert local_session.query(PlacesTerm).filter(PlacesTerm.id == 177).first() is None
    # check if person are not deleted
    person_1 = local_session.query(Person).filter(Person.id == 269).first()
    person_2 = local_session.query(Person).filter(Person.id == 270).first()
    events_1 = local_session.query(Event).filter_by(person_id=person_1.id).all()
    events_2 = local_session.query(Event).filter_by(person_id=person_2.id).all()
    assert len(events_1) == 9
    assert len(events_2) == 16
    assert person_1 is not None
    assert person_2 is not None

# -- Thesaurus terms --


def test_create_update_thesaurus_term():
    """Test create and update thesaurus person term and thesaurus places."""
    place_term = "Chateau fort"
    thesaurus_term = "chevalier"
    term = local_session.query(ThesaurusTerm).filter(ThesaurusTerm.term == thesaurus_term).first()
    assert term is None
    term = ThesaurusTerm(topic="Statut", term=thesaurus_term)
    local_session.add(term)
    local_session.commit()
    term = local_session.query(ThesaurusTerm).filter(ThesaurusTerm.term == thesaurus_term).first()
    assert term is not None
    assert term.term == thesaurus_term
    assert term.topic == "Statut"
    pl_term = local_session.query(PlacesTerm).filter(PlacesTerm.term == place_term).first()
    assert pl_term is None
    pl_term = PlacesTerm(topic="Domaine", term=place_term)
    local_session.add(pl_term)
    local_session.commit()
    pl_term = local_session.query(PlacesTerm).filter(PlacesTerm.term == place_term).first()
    assert pl_term is not None
    assert pl_term.term == place_term
    assert pl_term.topic == "Domaine"
    # update term
    term.topic = "Dignité"
    local_session.commit()
    term = local_session.query(ThesaurusTerm).filter(ThesaurusTerm.term == thesaurus_term).first()
    assert term is not None
    assert term.term == thesaurus_term
    assert term.topic == "Dignité"
    # update place term
    pl_term.topic = "Cloître"
    local_session.commit()
    pl_term = local_session.query(PlacesTerm).filter(PlacesTerm.term == place_term).first()
    assert pl_term is not None
    assert pl_term.term == place_term
    assert pl_term.topic == "Cloître"
    # update term with same topic
    term.topic = "Dignité"
    local_session.commit()
    term = local_session.query(ThesaurusTerm).filter(ThesaurusTerm.term == thesaurus_term).first()
    assert term is not None
    assert term.term == thesaurus_term
    assert term.topic == "Dignité"
    # update place term with same topic
    pl_term.topic = "Cloître"
    local_session.commit()
    pl_term = local_session.query(PlacesTerm).filter(PlacesTerm.term == place_term).first()
    assert pl_term is not None
    assert pl_term.term == place_term
    assert pl_term.topic == "Cloître"
    # delete term
    local_session.delete(term)
    local_session.commit()
    term = local_session.query(ThesaurusTerm).filter(ThesaurusTerm.term == thesaurus_term).first()
    assert term is None
    # delete place term
    local_session.delete(pl_term)
    local_session.commit()
    pl_term = local_session.query(PlacesTerm).filter(PlacesTerm.term == place_term).first()
    assert pl_term is None


def test_persistent_endp_id():
    """Check persistence endp_id and new endp_id."""
    # create new person
    person = Person(pref_label="TEST PERSON",
                    forename_alt_labels="test;TEST;test1",
                    surname_alt_labels="testa, testb",
                    )
    local_session.add(person)
    local_session.commit()
    assert person._id_endp is not None
    person_endp_id = person._id_endp
    person = local_session.query(Person).filter(Person._id_endp == person_endp_id).first()
    assert person is not None
    assert person._id_endp == person_endp_id
    # update person
    person.pref_label = "TEST PERSON 2"
    local_session.commit()
    person = local_session.query(Person).filter(Person._id_endp == person_endp_id).first()
    assert person is not None
    assert person._id_endp == person_endp_id
    assert person.pref_label == "TEST PERSON 2"
    # delete person
    local_session.delete(person)
    local_session.commit()
    person = local_session.query(Person).filter(Person._id_endp == person_endp_id).first()
    assert person is None


def test_family_relationships():
    person_1 = local_session.query(Person).filter(Person.id == 93).first()
    person_2 = local_session.query(Person).filter(Person.id == 94).first()
    person_3 = local_session.query(Person).filter(Person.id == 99).first()
    person_related_1 = local_session.query(Person).filter(Person.id == 95).first()
    person_related_2 = local_session.query(Person).filter(Person.id == 96).first()
    assert person_1 is not None
    assert person_2 is not None
    new_family_relationship_1 = PersonHasFamilyRelationshipType(
        person_id=person_1.id,
        relative_id=person_related_1.id,
        relation_type="fils de")
    new_family_relationship_2 = PersonHasFamilyRelationshipType(
        person_id=person_2.id,
        relative_id=person_related_1.id,
        relation_type="mère de")
    local_session.add(new_family_relationship_1)
    local_session.add(new_family_relationship_2)
    local_session.commit()
    family_relationship_1 = local_session.query(PersonHasFamilyRelationshipType).filter_by(
        person_id=person_1.id
    )
    family_relationship_2 = local_session.query(PersonHasFamilyRelationshipType).filter_by(
        person_id=person_2.id
    )
    assert family_relationship_1 is not None
    assert family_relationship_2 is not None
    # remove related person
    local_session.delete(person_related_1)
    local_session.commit()
    family_relationships_related = local_session.query(PersonHasFamilyRelationshipType).filter_by(
        relative_id=person_related_1.id
    ).all()
    assert family_relationships_related == []
    # check if persons are not deleted
    person_1 = local_session.query(Person).filter(Person.id == 93).first()
    person_2 = local_session.query(Person).filter(Person.id == 94).first()
    assert person_1 is not None
    assert person_2 is not None
    # remove person 1
    local_session.delete(person_1)
    local_session.commit()
    family_relationships_per_1 = local_session.query(PersonHasFamilyRelationshipType).filter_by(
        person_id=person_1.id
    ).all()
    assert family_relationships_per_1 == []
    # add relationship with person 3
    new_family_relationship_3 = PersonHasFamilyRelationshipType(
        person_id=person_3.id,
        relative_id=person_related_2.id,
        relation_type="fils de")
    local_session.add(new_family_relationship_3)
    local_session.commit()
    # test if relationship is added
    family_relationship_3 = local_session.query(PersonHasFamilyRelationshipType).filter_by(
        person_id=person_3.id,
        relative_id=person_related_2.id,
    ).first()
    assert family_relationship_3 is not None
    # update relationship
    family_relationship_3.relation_type = "fille de"
    local_session.commit()
    family_relationship_3 = local_session.query(PersonHasFamilyRelationshipType).filter_by(
        person_id=person_3.id,
        relative_id=person_related_2.id,
    ).first()
    assert family_relationship_3 is not None
    assert family_relationship_3.relation_type == "fille de"


def test_insert_model_constraint():
    person_1 = local_session.query(Person).filter(Person.id == 123).first()
    person_2_related = local_session.query(Person).filter(Person.id == 128).first()
    # check ";" separator in labels for person
    assert len(person_1.forename_alt_labels.split(';')) == 2
    # - update person 1
    person_1.forename_alt_labels = "test;TEST;test1"
    local_session.commit()
    person_1 = local_session.query(Person).filter(Person.id == 123).first()
    assert len(person_1.forename_alt_labels.split(';')) == 3
    # check unique reference integrity (jean d'acy fils de marie d'acy, jean d'acy père de marie d'acy)
    new_family_relationship_1 = PersonHasFamilyRelationshipType(
        person_id=person_1.id,
        relative_id=person_2_related.id,
        relation_type="fils de")
    new_family_relationship_2 = PersonHasFamilyRelationshipType(
        person_id=person_1.id,
        relative_id=person_2_related.id,
        relation_type="père de")
    with pytest.raises(IntegrityError):
        local_session.add(new_family_relationship_1)
        local_session.add(new_family_relationship_2)
        local_session.commit()

    local_session.rollback()
    # check if family relationship is not added
    family_relationship_1 = local_session.query(PersonHasFamilyRelationshipType).filter_by(
        person_id=person_1.id,
        relative_id=person_2_related.id,
        relation_type="fils de"
    ).first()
    family_relationship_2 = local_session.query(PersonHasFamilyRelationshipType).filter_by(
        person_id=person_1.id,
        relative_id=person_2_related.id,
        relation_type="père de"
    ).first()
    assert family_relationship_1 is None
    assert family_relationship_2 is None
    # check double in family relationship (jean d'acy fils de marie d'acy, jean d'acy fils de marie d'acy)
    new_family_relationship_1 = PersonHasFamilyRelationshipType(
        person_id=person_1.id,
        relative_id=person_2_related.id,
        relation_type="fils de")
    new_family_relationship_2 = PersonHasFamilyRelationshipType(
        person_id=person_1.id,
        relative_id=person_2_related.id,
        relation_type="fils de")
    with pytest.raises(IntegrityError):
        local_session.add(new_family_relationship_1)
        local_session.add(new_family_relationship_2)
        local_session.commit()
    local_session.rollback()
    # check if family relationships are not added
    family_relationship_1 = local_session.query(PersonHasFamilyRelationshipType).filter_by(
        person_id=person_1.id,
        relative_id=person_2_related.id,
        relation_type="fils de"
    ).first()
    family_relationship_2 = local_session.query(PersonHasFamilyRelationshipType).filter_by(
        person_id=person_1.id,
        relative_id=person_2_related.id,
        relation_type="fils de"
    ).first()
    assert family_relationship_1 is None
    assert family_relationship_2 is None
    # check circular reference with family relationship (jean d'acy fils de jean d'acy)
    new_family_relationship_1 = PersonHasFamilyRelationshipType(
        person_id=person_1.id,
        relative_id=person_1.id,
        relation_type="fils de")
    with pytest.raises(IntegrityError):
        local_session.add(new_family_relationship_1)
        local_session.commit()
    local_session.rollback()
    # check if family relationship is not added
    family_relationship_1 = local_session.query(PersonHasFamilyRelationshipType).filter_by(
        person_id=person_1.id,
        relative_id=person_1.id,
        relation_type="fils de"
    ).first()
    assert family_relationship_1 is None






