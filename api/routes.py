"""
routes.py

Api endpoints.
"""
from typing import List
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
                   get_family_relatives)
from .schemas import (PersonOut,
                      Message,
                      PersonSearchOut, 
                      ThesaurusMeta,
                      PersonEventsOut,
                      PersonFamilyRelationshipsOut,
                      TYPE_SEARCH,
                      TYPE_THESAURUS)
from .index_fts.search_utils import search_index
from .index_conf import st
from .api_meta import METADATA
from .models import PlacesTerm

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
async def search(
    query: str = Query(default=""),
    type_query: TYPE_SEARCH = Query(default="exact"),
    only_canon: bool = False,
    place_ids: List[str] = Query(default=[]),
    person_term_ids: List[str] = Query(default=[]),
    db: Session = Depends(get_db)
):
    try:
        if query == "":
            persons = get_persons(db, only_canon=only_canon)
        else:
            ix = st.open_index()
            search_results = search_index(
            ix=ix,
            query_user=query,
            search_type=type_query.value,
            fieldnames=["pref_label", "forename_alt_labels", "surname_alt_labels"]
        )
            ix.close()

            persons = [get_person(db, {'id': result['id']}) for result in search_results]
            persons = [p for p in persons if p is not None]

        if only_canon:
            persons = [p for p in persons if p.is_canon]

        print(persons)

        # -- Filtering helpers --

        def person_has_all_places(person, required_place_ids):
            person_place_ids = {
                e.place_term._id_endp
                for e in person.events if e.place_term is not None
            }
            return all(pid in person_place_ids for pid in required_place_ids)

        def person_has_all_thesaurus_terms(person, required_term_ids):
            person_term_ids = {
                e.thesaurus_term_person._id_endp
                for e in person.events if e.thesaurus_term_person is not None
            }
            return all(tid in person_term_ids for tid in required_term_ids)

        # -- Faceted filtering (AND logic) --
        if place_ids:
            persons = [p for p in persons if person_has_all_places(p, place_ids)]

        if person_term_ids:
            persons = [p for p in persons if person_has_all_thesaurus_terms(p, person_term_ids)]

        return paginate(persons)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"It seems the server has trouble: {e}"}
        )

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
            return JSONResponse(status_code=404, content={"message": f"Events related to person with id '{_id_endp}' not found."})
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
            return JSONResponse(status_code=404, content={"message": f"Family relationships related to person with id '{_id_endp}' not found."})
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
                            content={"message": f"Thesaurus term with _endp_id '{_id_endp}' not found in thesaurus '{thesaurus_type.value}'."})
    else:
        return JSONResponse(status_code=500,
                            content={"message": "It seems the server have trouble."})



@api_router.get("/places/map_places",
                tags=["places"],
                summary="Récupérer les lieux et les événements d'une personne associés à ce lieu.")
async def get_map_places(
    db: Session = Depends(get_db),
    map_place_label_id: str = Query(default=None)
):
    """
    Cette route est conçue pour les expérimentations avec le laboratoire MAP (CNRS).
    Elle permet de récupérer les lieux et les événements associés à ce lieu.
    Par défaut, la route renvoie tous les lieux et événements qui ont un id MAP.
    Si un id MAP est fourni (exemple, `CA27`), la route renvoie uniquement les événements associés à ce lieu.
    """
    try:
        query = db.query(PlacesTerm).filter(PlacesTerm.map_place_label_id != None)
        if map_place_label_id:
            query = query.filter(PlacesTerm.map_place_label_id == map_place_label_id)

        places = query.all()

        results = []
        for place in places:
            events = place.events
            event_list = []
            for e in events:
                event_list.append({
                    "id_endp": e._id_endp,
                    "date": e.date,
                    "type": e.type,
                    "thesaurus_term_person": {
                        "id_endp": e.thesaurus_term_person._id_endp,
                        "term": e.thesaurus_term_person.term,
                        "term_fr": e.thesaurus_term_person.term_fr
                    } if e.thesaurus_term_person else None,
                    "image_url": e.image_url,
                    "comment": e.comment,
                    "person": {
                        "id_endp": e.person._id_endp,
                        "pref_label": e.person.pref_label
                    } if e.person else None,
                    "facsimile_url": (
                        f"https://dev.chartes.psl.eu/endp/facsimile/{e.image_url.split(';')[0]}/"
                        f"{e.image_url.split(';')[0][2:] if e.image_url else ''}"
                    ) if e.image_url and ';' in e.image_url else None
                })

            results.append({
                "id_endp": place._id_endp,
                "topic": place.topic,
                "term": place.term,
                "term_fr": place.term_fr,
                "term_definition": place.term_definition,
                "map_place_label_id": place.map_place_label_id,
                "map_place_label_new": place.map_place_label_new,
                "map_place_label_old": place.map_place_label_old,
                "map_place_before_restore_url": place.map_place_before_restore_url,
                "map_place_after_restore_url": place.map_place_after_restore_url,
                "map_place_ark": place.map_place_ark,
                "events": event_list
            })

        return {"items": results}

    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Erreur serveur : {str(e)}"})
