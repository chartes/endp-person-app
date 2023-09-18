"""
routes.py

Api endpoints.
"""
from fastapi import (APIRouter,
                     Depends)
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
def read_root():
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
                response_model=PersonSearchOut,
                tags=["persons"],
                responses={500: {"model": Message}},
                summary=METADATA_ROUTES["search"]["summary"])
async def search(query: str, type_query: TYPE_SEARCH, db: Session = Depends(get_db)):
    try:
        ix = st.open_index()
        search_results = search_index(
            ix=ix,
            query_user=query,
            search_type=type_query.value,
            fieldnames=["pref_label", "forename_alt_labels", "surname_alt_labels"]
        )
        results = search_results
        # print(results)
        search_results = [
            get_person(db,
                       {'id': result['id']}) for result in results
        ]
        # print(search_results)
        search_results = [person for person in search_results if person is not None]
        ix.close()
        return {"query": query,
                "total": len(search_results),
                "type_query": type_query.value,
                "results": search_results
                }
    except Exception as e:
        return JSONResponse(status_code=500,
                            content={"message": "It seems the server have trouble: "
                                                f"{e}"})


@api_router.get("/persons/",
                response_model=Page[PersonOut],
                responses={500: {"model": Message}},
                tags=["persons"],
                summary=METADATA_ROUTES["read_persons"]["summary"])
async def read_persons(db: Session = Depends(get_db)):
    try:
        return paginate(get_persons(db))
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
        return get_person(db, {"_id_endp": _id_endp})
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

