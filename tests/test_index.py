"""
Tests synchronization between database and fts index.
"""
from api.index_conf import st
from api.index_fts.search_utils import search_index
from api.crud import get_person
from api.models import Person

from tests.conftest import local_session


def get_results(query, type_query):
    ix = st.open_index()
    results = search_index(ix=ix,
                           query_user=query,
                           search_type=type_query,
                           fieldnames=["pref_label",
                                       "forename_alt_labels",
                                       "surname_alt_labels"])
    with local_session as session:
        search_results = [
            get_person(session,
                       {'id': result['id']}) for result in results
        ]
    return search_results


def test_index_search():
    search_results = get_results(query="jean",
                                 type_query="exact")
    print(search_results)
    assert len(search_results) == 10
    assert search_results[0].pref_label == "Jean Chanteprime"


def test_index_create():
    with local_session as session:
        person = Person(
            pref_label="Jean Giono",
            forename_alt_labels="Jehan;johan;jeha",
            surname_alt_labels="Gieno;Giena;Giauno",
        )
        session.add(person)
        session.commit()
    search_results = get_results(query="Jean Giono",
                                 type_query="exact")
    assert "Jean Giono" in [result.pref_label for result in search_results]
    search_results = get_results(query="jehan gioni",
                                 type_query="fuzzy")
    assert "Jean Giono" in [result.pref_label for result in search_results]


def test_update_index():
    with local_session as session:
        person = session.query(Person).filter(Person.pref_label == "Jean Giono").first()
        person.pref_label = "Jean Gioni"
        session.commit()
    search_results = get_results(query="Jean Giono",
                                 type_query="exact")
    assert "Jean Giono" not in [result.pref_label for result in search_results]
    search_results = get_results(query="Jean Gioni",
                                 type_query="exact")
    assert "Jean Gioni" in [result.pref_label for result in search_results]


def test_index_delete():
    with local_session as session:
        person = session.query(Person).filter(Person.pref_label == "Jean Gioni").first()
        session.delete(person)
        session.commit()
    search_results = get_results(query="Jean Gioni",
                                 type_query="exact")
    assert len(search_results) == 0
    search_results = get_results(query="jean gioni",
                                 type_query="fuzzy")
    assert len(search_results) != 0
    assert "Jean Gioni" not in [result.pref_label for result in search_results]
