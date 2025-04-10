"""
routes.py

Api endpoints.
"""
from typing import List
from collections import defaultdict

from fastapi import (APIRouter,
                     Depends,
                     Query)
from fastapi.responses import JSONResponse
from fastapi_pagination import (Page,
                                paginate)
from fastapi_pagination.utils import disable_installed_extensions_check

disable_installed_extensions_check()

from sqlalchemy.orm import Session

from .database import get_db
from .crud import (get_person,
                   get_persons,
                   get_thesaurus_terms,
                   get_thesaurus_term,
                   get_events,
                   get_family_relatives,
                   get_freq_terms_from_persons,
                   get_persons_filtered_by_events)
from .schemas import (PersonOut,
                      Message,
                      EventMeta,
                      PersonMeta,
                      PersonSearchOut,
                      ThesaurusMeta,
                      PersonEventsOut,
                      PersonFamilyRelationshipsOut,
                      TYPE_SEARCH,
                      TYPE_THESAURUS,
                      TYPE_GROUP_BY,
                      TYPE_TOPIC_LABELS)
from .index_fts.search_utils import search_index
from .index_conf import st
from .api_meta import METADATA

from .models import (Person,
                     Event,
                     PlacesTerm,
                     ThesaurusTerm)

api_router = APIRouter()

METADATA_ROUTES = METADATA["routes"]


# -- protected routes --
@api_router.get("/meta/persons/person/{_endp_id}",
                include_in_schema=False,
                responses={404: {"model": Message}},
                summary=METADATA_ROUTES["get_meta_person"]["summary"])
async def get_meta_person(person_id: str, db: Session = Depends(get_db)):
    person = get_person(db, {"_id_endp": person_id})
    if person is None:
        return JSONResponse(status_code=404,
                            content={"message": f"Person with id {person_id} not found."})
    return {
        "person_id_endp": person._id_endp,
        "person_id_db": person.id,
        "person_edit_db_path": f"/admin/person/edit/?id={person.id}&url=/admin/person/",
        "person_show_db_path": f"/admin/person/details/?id={person.id}&url=/admin/person/"
    }


@api_router.get("/",
                responses={500: {"model": Message}, 200: {"model": Message}},
                summary=METADATA_ROUTES["read_root"]["summary"])
async def read_root():
    # try if the server is up
    try:
        return JSONResponse(status_code=200,
                            content={"message": "Welcome to e-NDP person API!"}
                            )
    except Exception as e:
        return JSONResponse(status_code=500,
                            content={"message": "The service is not available, "
                                                f"try again later. "
                                                f"- {e}"})


@api_router.get('/persons/search',
                response_model=Page[PersonOut],
                tags=["persons"],
                responses={500: {"model": Message}},
                summary=METADATA_ROUTES["search"]["summary"])
async def search(query: str, type_query: TYPE_SEARCH, only_canon: bool = False, db: Session = Depends(get_db)):
    try:
        ix = st.open_index()
        search_results = search_index(
            ix=ix,
            query_user=query,
            search_type=type_query.value,
            fieldnames=["pref_label", "forename_alt_labels", "surname_alt_labels"]
        )
        results = search_results
        search_results = [
            get_person(db,
                       {'id': result['id']}) for result in results
        ]
        if only_canon:
            search_results = [person for person in search_results if person.is_canon]

        search_results = [person for person in search_results if person is not None]
        ix.close()
        # return {"query": query,
        #        "total": len(search_results),
        #        "type_query": type_query.value,
        #        "results": search_results
        #        }
        return paginate(search_results)
    except Exception as e:
        return JSONResponse(status_code=500,
                            content={"message": "It seems the server have trouble: "
                                                f"{e}"})


@api_router.get("/persons/",
                response_model=Page[PersonOut],
                responses={500: {"model": Message}},
                tags=["persons"],
                summary=METADATA_ROUTES["read_persons"]["summary"])
async def read_persons(only_canon: bool = False, db: Session = Depends(get_db)):
    try:
        persons = get_persons(db, only_canon=only_canon)
        return paginate(persons)
    except Exception as e:
        return JSONResponse(status_code=500,
                            content={"message": "It seems the server have trouble: "
                                                f"{e}"})


@api_router.get("/persons/person/{_id_endp}",
                response_model=PersonOut,
                responses={404: {"model": Message}, 500: {"model": Message}},
                tags=["persons"],
                summary=METADATA_ROUTES["read_person"]["summary"])
async def read_person(db: Session = Depends(get_db), _id_endp: str = ""):
    try:
        person = get_person(db, {"_id_endp": _id_endp})
        if person is None:
            return JSONResponse(status_code=404, content={"message": "Person not found."})
        return person
    except Exception as e:
        return JSONResponse(status_code=500,
                            content={"message": "It seems the server have trouble: "
                                                f"{e}"})


# test for filtered persons
@api_router.get("/persons/persons_filtered",
                response_model=Page[PersonOut],
                include_in_schema=True,
                responses={404: {"model": Message}, 500: {"model": Message}},
                tags=["persons"])
async def read_persons_filtered(
        db: Session = Depends(get_db),
        combine: bool = False,
        only_canon: bool = False,
        place_terms: List[str] = Query(default=None),
        thesaurus_terms_person: List[str] = Query(default=None)
):
    """
    Fetch filtered persons based on place_terms and thesaurus_terms_person.
    """
    print(f"combine: {combine}")
    print(f"only_canon: {only_canon}")
    print(f"place_terms: {place_terms}")
    print(f"thesaurus_terms_person: {thesaurus_terms_person}")
    try:
        persons = get_persons_filtered_by_events(
            db=db,
            only_canon=only_canon,
            place_terms=place_terms,
            thesaurus_terms_person=thesaurus_terms_person,
            combine_filters_with_or=combine
        )
        return paginate(persons)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"It seems the server have trouble: {e}"}
        )


# ~ PERSONS RELATIONS ENDPOINTS (EVENTS / FAMILY RELATIONSHIPS) ~


@api_router.get("/persons/person/{_id_endp}/events",
                response_model=PersonEventsOut,
                responses={404: {"model": Message}, 500: {"model": Message}},
                tags=["persons relations"],
                summary=METADATA_ROUTES["read_person_events"]["summary"])
async def read_person_events(db: Session = Depends(get_db), _id_endp: str = ""):
    try:
        events = get_events(db, {"_id_endp": _id_endp})
        if events is None:
            return JSONResponse(status_code=404,
                                content={"message": f"Events related to person with id '{_id_endp}' not found."})
        return events
    except Exception as e:
        return JSONResponse(status_code=500,
                            content={"message": "It seems the server have trouble: "
                                                f"{e}"})


@api_router.get("/persons/person/{_id_endp}/family_relationships",
                response_model=PersonFamilyRelationshipsOut,
                responses={404: {"model": Message}, 500: {"model": Message}},
                tags=["persons relations"],
                summary=METADATA_ROUTES["read_person_family_relationships"]["summary"]
                )
async def read_person_family_relationships(db: Session = Depends(get_db), _id_endp: str = ""):
    try:
        relatives = get_family_relatives(db, {"_id_endp": _id_endp})
        if relatives is None:
            return JSONResponse(status_code=404, content={
                "message": f"Family relationships related to person with id '{_id_endp}' not found."})
        return relatives
    except Exception as e:
        return JSONResponse(status_code=500,
                            content={"message": "It seems the server have trouble: "
                                                f"{e}"})


# ~ PERSONS THESAURI ENDPOINTS ~

@api_router.get("/persons/thesauri/terms",
                response_model=Page[ThesaurusMeta],
                responses={500: {"model": Message}},
                tags=["persons thesauri"],
                summary=METADATA_ROUTES["read_person_thesauri_terms"]["summary"])
async def read_person_thesauri_terms(thesaurus_type: TYPE_THESAURUS, db: Session = Depends(get_db)):
    thesaurus_terms = get_thesaurus_terms(db=db, model=thesaurus_type.value)
    if thesaurus_terms is not None:
        return paginate(thesaurus_terms)
    else:
        return JSONResponse(status_code=500,
                            content={"message": "It seems the server have trouble."})


@api_router.get("/persons/thesauri/term/{_id_endp}",
                response_model=ThesaurusMeta,
                responses={404: {"model": Message}, 500: {"model": Message}},
                tags=["persons thesauri"],
                summary=METADATA_ROUTES["read_person_thesaurus_term"]["summary"])
async def read_person_thesaurus_term(thesaurus_type: TYPE_THESAURUS, _id_endp: str = "", db: Session = Depends(get_db)):
    thesaurus_term = get_thesaurus_term(db=db, model=thesaurus_type.value, args={"_id_endp": _id_endp})
    if thesaurus_term is not None:
        return thesaurus_term
    elif thesaurus_term is None:
        return JSONResponse(status_code=404,
                            content={
                                "message": f"Thesaurus term with _endp_id '{_id_endp}' not found in thesaurus '{thesaurus_type.value}'."})
    else:
        return JSONResponse(status_code=500,
                            content={"message": "It seems the server have trouble."})


# Experimental routes for maps

@api_router.get("/persons/events",
                response_model=Page,  # Pagination activée
                responses={500: {"model": Message}},
                tags=["persons relations"],
                summary="Obtenir les personnes avec leurs événements filtrés par thesaurus_type, topic et group_by avec pagination")
async def get_persons_with_events(
        thesaurus_type: TYPE_THESAURUS,
        topic: TYPE_TOPIC_LABELS,
        group_by: TYPE_GROUP_BY,  # "person" ou "term"
        db: Session = Depends(get_db)
):
    """
    Retourne une liste paginée de personnes avec leurs événements associés, filtrée par `thesaurus_type` et `topic`.

    - `thesaurus_type` : Type du thésaurus (`places` ou `persons_terms`)
    - `topic` : Sujet du thésaurus (ex. "Cloître", "Prévôté", etc.)
    - `group_by` : Mode de regroupement (`person` ou `term`)
    """
    try:
        if group_by.value not in ["person", "term"]:
            return JSONResponse(status_code=400, content={"message": "Paramètre group_by invalide. Utilisez 'person' ou 'term'."})

        # Sélection du modèle de thésaurus et du filtre d'événement en fonction du thesaurus_type
        if thesaurus_type == TYPE_THESAURUS.places:
            thesaurus_model = PlacesTerm
            event_filter = Event.place_term_id
        elif thesaurus_type == TYPE_THESAURUS.persons_terms:
            thesaurus_model = ThesaurusTerm
            event_filter = Event.person_thesaurus_term_id
        else:
            return JSONResponse(status_code=400, content={"message": "Thesaurus type invalide"})

        topic = topic.value

        # Récupération des termes de thésaurus associés au topic
        thesaurus_terms = db.query(thesaurus_model).filter(thesaurus_model.topic == topic).all()

        if not thesaurus_terms:
            return JSONResponse(status_code=404, content={"message": f"Aucun terme trouvé pour topic '{topic}'"})

        thesaurus_term_ids = [term.id for term in thesaurus_terms]

        # Récupération des événements qui sont liés à ces termes
        events = db.query(Event).filter(event_filter.in_(thesaurus_term_ids)).all()

        if not events:
            return JSONResponse(status_code=404, content={"message": f"Aucun événement trouvé pour topic '{topic}'"})

        # Récupération des personnes concernées par ces événements
        person_ids = {event.person_id for event in events}
        persons = db.query(Person).filter(Person.id.in_(person_ids)).all()

        # Création de mappings pour éviter des requêtes inutiles
        persons_dict = {person.id: person for person in persons}
        terms_dict = {term.id: term for term in thesaurus_terms}

        # Initialisation de la réponse
        response_data = []

        if group_by.value == "person":
            # Groupement par personne
            response_data = [
                {
                    "id_endp": person._id_endp,
                    "pref_label": person.pref_label,
                    "events": [
                        {
                            "id_endp": event._id_endp,
                            "date": event.date,
                            "type": event.type,
                            "place_term": (
                                {
                                    "id_endp": event.place_term._id_endp,
                                    "term": event.place_term.term,
                                    "term_fr": event.place_term.term_fr,
                                    "map_chap_nomenclature_id": event.place_term.map_chap_nomenclature_id,
                                    "map_chap_label_new": event.place_term.map_chap_label_new,
                                    "map_chap_label_old": event.place_term.map_chap_label_old,
                                    "map_chap_before_restore_url": event.place_term.map_chap_before_restore_url,
                                    "map_chap_after_restore_url": event.place_term.map_chap_after_restore_url
                                } if event.place_term else None
                            ),
                            "thesaurus_term_person": (
                                {
                                    "id_endp": event.thesaurus_term_person._id_endp,
                                    "term": event.thesaurus_term_person.term,
                                    "term_fr": event.thesaurus_term_person.term_fr
                                } if event.thesaurus_term_person else None
                            ),
                            "image_url": event.image_url,
                            "comment": event.comment
                        }
                        for event in events if event.person_id == person.id
                    ]
                }
                for person in persons
            ]
        else:
            # Groupement par terme de thésaurus (places ou persons_terms)
            grouped_by_term = defaultdict(lambda: defaultdict(list))

            for event in events:
                term_id = event.place_term_id if thesaurus_type == TYPE_THESAURUS.places else event.person_thesaurus_term_id
                if term_id:
                    grouped_by_term[term_id][event.person_id].append({
                        "id_endp": event._id_endp,
                        "date": event.date,
                        "type": event.type,
                        "place_term": (
                            {
                                "id_endp": event.place_term._id_endp,
                                "term": event.place_term.term,
                                "term_fr": event.place_term.term_fr,
                                "map_chap_nomenclature_id": event.place_term.map_chap_nomenclature_id,
                                "map_chap_label_new": event.place_term.map_chap_label_new,
                                "map_chap_label_old": event.place_term.map_chap_label_old,
                                "map_chap_before_restore_url": event.place_term.map_chap_before_restore_url,
                                "map_chap_after_restore_url": event.place_term.map_chap_after_restore_url
                            } if event.place_term else None
                        ),
                        "thesaurus_term_person": (
                            {
                                "id_endp": event.thesaurus_term_person._id_endp,
                                "term": event.thesaurus_term_person.term,
                                "term_fr": event.thesaurus_term_person.term_fr
                            } if event.thesaurus_term_person else None
                        ),
                        "image_url": event.image_url,
                        "comment": event.comment
                    })

            for term_id, term_persons in grouped_by_term.items():
                term_obj = terms_dict.get(term_id)
                if term_obj:
                    response_data.append({
                        "id_endp": term_obj._id_endp,
                        "topic": term_obj.topic,
                        "term": term_obj.term,
                        "term_fr": term_obj.term_fr,
                        "term_definition": term_obj.term_definition,
                        "map_chap_nomenclature_id": term_obj.map_chap_nomenclature_id,
                        "map_chap_label_new": term_obj.map_chap_label_new,
                        "map_chap_label_old": term_obj.map_chap_label_old,
                        "map_chap_before_restore_url": term_obj.map_chap_before_restore_url,
                        "map_chap_after_restore_url": term_obj.map_chap_after_restore_url,
                        "persons": [
                            {
                                "id_endp": persons_dict[person_id]._id_endp,
                                "pref_label": persons_dict[person_id].pref_label,
                                "events": events_list
                            }
                            for person_id, events_list in term_persons.items() if person_id in persons_dict
                        ]
                    })

        return paginate(response_data)

    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Erreur serveur: {e}"})

@api_router.get("/persons/events/by-thesaurus-id",
                responses={500: {"model": Message}},
                tags=["persons relations"],
                summary="Obtenir les personnes et événements liés à un ID de thésaurus avec total personnes et événements")
async def get_persons_by_thesaurus_id(
        thesaurus_id_endp: str,
        thesaurus_type: TYPE_THESAURUS,
        db: Session = Depends(get_db)
):
    """
    Retourne toutes les personnes et leurs événements associés en fonction de `thesaurus_id_endp`.

    - `thesaurus_id_endp` : ID endp du terme de thésaurus (ex. id d'une Chapelle)
    - `thesaurus_type` : Type du thésaurus (`places` ou `persons_terms`)
    """
    try:
        # Définition du modèle de thésaurus
        if thesaurus_type == TYPE_THESAURUS.places:
            thesaurus_model = PlacesTerm
            event_filter = Event.place_term_id
        elif thesaurus_type == TYPE_THESAURUS.persons_terms:
            thesaurus_model = ThesaurusTerm
            event_filter = Event.person_thesaurus_term_id
        else:
            return JSONResponse(status_code=400, content={"message": "Thesaurus type invalide"})

        # Récupération du terme de thésaurus par son ID endp
        thesaurus_term = db.query(thesaurus_model).filter(thesaurus_model._id_endp == thesaurus_id_endp).first()

        if not thesaurus_term:
            return JSONResponse(status_code=404, content={"message": f"Aucun terme trouvé pour ID '{thesaurus_id_endp}'"})

        # Récupération des événements liés à ce terme
        events = db.query(Event).filter(event_filter == thesaurus_term.id).all()

        if not events:
            return JSONResponse(status_code=404, content={"message": f"Aucun événement trouvé pour ID '{thesaurus_id_endp}'"})

        # Récupération des personnes concernées par ces événements
        person_ids = {event.person_id for event in events}
        persons = db.query(Person).filter(Person.id.in_(person_ids)).all()

        # Mapping personnes par ID pour accès rapide
        persons_dict = {person.id: person for person in persons}

        # Structure de la réponse
        response_data = {
            "thesaurus_term": {
                "id_endp": thesaurus_term._id_endp,
                "topic": thesaurus_term.topic,
                "term": thesaurus_term.term,
                "term_fr": thesaurus_term.term_fr,
                "term_definition": thesaurus_term.term_definition
            },
            "total_persons": len(persons),  # Nombre total de personnes concernées
            "total_events": len(events),  # Nombre total d'événements liés
            "persons": [
                {
                    "id_endp": person._id_endp,
                    "pref_label": person.pref_label,
                    "events": [
                        {
                            "id_endp": event._id_endp,
                            "date": event.date,
                            "type": event.type,
                            "image_url": event.image_url,
                            "comment": event.comment
                        }
                        for event in events if event.person_id == person.id
                    ]
                }
                for person in persons
            ]
        }

        """
        if thesaurus type == places and topic == CHAPELLE 
        => add to response in thesaurus term section 
        map_chap_nomenclature_id = Column(String, nullable=False, unique=False)
    map_chap_label_new = Column(String, nullable=False, unique=False)
    map_chap_label_old = Column(String, nullable=False, unique=False)
    map_chap_before_restore_url = Column(String, nullable=False, unique=False)
    map_chap_after_restore_url = Column(String, nullable=False, unique=False)

        """
        if thesaurus_type == TYPE_THESAURUS.places:
                response_data["thesaurus_term"]["map_chap_nomenclature_id"] = thesaurus_term.map_chap_nomenclature_id
                response_data["thesaurus_term"]["map_chap_label_new"] = thesaurus_term.map_chap_label_new
                response_data["thesaurus_term"]["map_chap_label_old"] = thesaurus_term.map_chap_label_old
                response_data["thesaurus_term"]["map_chap_before_restore_url"] = thesaurus_term.map_chap_before_restore_url
                response_data["thesaurus_term"]["map_chap_after_restore_url"] = thesaurus_term.map_chap_after_restore_url

        return response_data

    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Erreur serveur: {e}"})

@api_router.get("/persons/thesauri/terms/all",
                response_model=List[ThesaurusMeta],  # Liste complète sans pagination
                responses={500: {"model": Message}},
                tags=["persons thesauri"],
                summary="Obtenir tous les termes de thésaurus filtrés par type et topic")
async def read_all_person_thesauri_terms(
    thesaurus_type: TYPE_THESAURUS,
    topic: TYPE_TOPIC_LABELS,
    db: Session = Depends(get_db)
):
    """
    Retourne **tous** les termes du thésaurus correspondant à un `thesaurus_type` donné,
    avec une option pour filtrer par `topic` (ex. "Chapelle", "Cloître", etc.).

    - **`thesaurus_type`** : Type de thésaurus (`places`, `persons_terms`)
    - **`topic`** *(optionnel)* : Filtrer les termes associés à un sujet spécifique

    📌 **Exemple d'utilisation :**
    - `/persons/thesauri/terms/all?thesaurus_type=places&topic=Chapelle`
    - `/persons/thesauri/terms/all?thesaurus_type=persons_terms`
    """
    try:
        if thesaurus_type == TYPE_THESAURUS.places:
            thesaurus_model = PlacesTerm
        elif thesaurus_type == TYPE_THESAURUS.persons_terms:
            thesaurus_model = ThesaurusTerm

        if topic:
            topic = topic.value
            query = db.query(thesaurus_model).filter(thesaurus_model.topic == topic)

            thesaurus_terms = query.all()

            if thesaurus_terms:
                return thesaurus_terms
            else:
                return JSONResponse(status_code=404, content={"message": "Aucun terme trouvé pour ces critères."})

    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Erreur serveur: {e}"})
