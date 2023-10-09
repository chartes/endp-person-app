"""
Tests API endp endpoints.
"""

from tests.conftest import client, local_session
from api.models import Person


def test_default():
    response = client.get("/")
    assert response.status_code == 404
    response = client.get("/endp-person/api/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to e-NDP person API!"
    }


def test_read_persons():
    response = client.get("/endp-person/api/persons/")
    assert response.status_code == 200
    response = client.get("/endp-person/api/persons/?page=1")
    assert response.status_code == 200
    response = client.get("/endp-person/api/persons/?page=1&size=10")
    assert response.status_code == 200
    response = client.get("/endp-person/api/persons/?page=1&size=1000")
    assert response.status_code == 422


def test_persons_search():
    response = client.get("/endp-person/api/persons/search?query=jean&type_query=exact")
    assert response.status_code == 200
    response = client.get("/endp-person/api/persons/search?query=jean&type_query=fuzzy")
    assert response.status_code == 200
    response = client.get("/endp-person/api/persons/search?query=jean&type_query=very_fuzzy")
    assert response.status_code == 200
    response = client.get("/endp-person/api/persons/search?query=jean&type_query=prefix")
    assert response.status_code == 422


def test_person():
    with local_session as session:
        person = session.query(Person).first()
        id_endp = person._id_endp
    response = client.get(f"/endp-person/api/persons/person/{id_endp}")
    assert response.status_code == 200
    response = client.get(f"/endp-person/api/persons/person/123")
    assert response.status_code == 404
    assert response.json() == {"message": "Person not found."}


def test_person_events():
    with local_session as session:
        person = session.query(Person).first()
        id_endp = person._id_endp
    response = client.get(f"/endp-person/api/persons/person/{id_endp}/events")
    assert response.status_code == 200
    response = client.get(f"/endp-person/api/persons/person/123/events")
    assert response.status_code == 404
    assert response.json() == {"message": "Events related to person with id '123' not found."}
    response = client.get(f"/endp-person/api/persons/person/events")
    assert response.status_code == 404


def test_person_family_relationships():
    with local_session as session:
        person = session.query(Person).first()
        id_endp = person._id_endp
    response = client.get(f"/endp-person/api/persons/person/{id_endp}/family_relationships")
    assert response.status_code == 200
    response = client.get(f"/endp-person/api/persons/person/123/family_relationships")
    assert response.status_code == 404
    assert response.json() == {"message": "Family relationships related to person with id '123' not found."}
    response = client.get(f"/endp-person/api/persons/person/family_relationships")
    assert response.status_code == 404


def test_persons_thesauri():
    response = client.get("/endp-person/api/persons/thesauri/terms?thesaurus_type=places&page=1&size=50")
    assert response.status_code == 200
    response = client.get("/endp-person/api/persons/thesauri/terms?thesaurus_type=persons_terms&page=1&size=50")
    assert response.status_code == 200
    response = client.get("/endp-person/api/persons/thesauri/terms?thesaurus_type=jobs&page=1&size=50")
    assert response.status_code == 422
    response = client.get("/endp-person/api/persons/thesauri/terms/persons/thesauri/terms?thesaurus_type=places&page=1&size=10000")
    assert response.status_code == 404


def test_persons_thesauri_term():
    pass