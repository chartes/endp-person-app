"""
routes.py

Api endpoints.
"""
from typing import List
from fastapi import (APIRouter,
                     Depends,
                     HTTPException,
                     Query)
from fastapi.responses import JSONResponse
from fastapi_pagination import (Page, paginate)
from fastapi_pagination.utils import disable_installed_extensions_check
disable_installed_extensions_check()

from sqlalchemy.orm import Session

from .database import get_db
from .crud import get_person, get_persons, get_event_by_person_id
from .schemas import PersonOut, EventScheme, Message

api_router = APIRouter()



@api_router.get("/",
                summary="Tester la disponibilité du service")
async def read_root():
    return {"message": "Bienvenue sur l'API e-NDP pour les personnes."}


@api_router.get("/persons/",
                response_model=Page[PersonOut],
                tags=["personnes"],
                summary="Retrouver la liste des personnes",
                description="Retrouver la liste des personnes avec pagination.")
async def read_persons(db: Session = Depends(get_db)):
    return paginate(get_persons(db))


@api_router.get("/persons/{person_id}",
                response_model=PersonOut,
                responses={404: {"model": Message}},
                tags=["personnes"])
async def read_person(db: Session = Depends(get_db), person_id: str = ""):
    """Permet de récupérer une personne par son identifiant endp"""
    person = get_person(db, {"_id_endp": person_id})
    if person is None:
        return JSONResponse(status_code=404, content={"message": "Person not found."})
    return get_person(db, {"_id_endp": person_id})

# - evenements pour une personne
# - liens familiaux pour une personne
# - les termes du thesaurus pour une personne
# - les termes du thesaurus lieux
