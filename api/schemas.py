"""
schemas.py

Pydantic models for API endpoints.
Use for validation and serialization.
"""

from typing import Union, List
from enum import Enum

from pydantic import BaseModel, Field, PrivateAttr

# -- parameters schema enums --
TYPE_SEARCH = Enum("TYPE_SEARCH", dict(
    exact="exact",
    fuzzy="fuzzy",
    very_fuzzy="very_fuzzy"
))

TYPE_THESAURUS = Enum("TYPE_THESAURUS", dict(
    places="places",
    persons_terms="persons_terms"
))

# TODO : 1) refactoriser les schemas pour les rendre plus génériques
#        2) enlever les exemples des champs préféré les types
#        3) vérifier les types des champs
#        4) ajouter les champs manquants
#        5) tester les specs openapi

# -- Generic schemas --


class Message(BaseModel):
    """Schema for error messages."""
    message: str

class PersonMeta(BaseModel):
    id_endp: str = Field(..., alias="_id_endp", example="person_endp_54r5rj8U")
    pref_label: str = Field(alias="pref_label", example="Jean d'Acy")

class MinimalMetaEvent(BaseModel):
    pass


class ThesaurusOut(BaseModel):
    id_endp: str = Field(..., alias="_id_endp")
    topic: str
    term: str = Field(..., alias="term_la")
    term_fr: Union[str, None] = Field(..., alias="term_fr")
    term_definition: Union[str, None] = Field(..., alias="definition")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

# -- Output schemas --


class KbMeta(BaseModel):
    id_endp: str = Field(..., alias="_id_endp")
    type_kb: str = Field(..., alias="type")
    url: str = Field(..., alias="url")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class EventMeta(BaseModel):
    id_endp: str = Field(..., alias="_id_endp")

    date: Union[str, None] = Field(..., alias="date")
    image_url: Union[str, None] = Field(..., alias="image_url")
    place_term: Union[ThesaurusOut, None] = Field(..., alias="place_term")
    thesaurus_term_person: Union[ThesaurusOut, None] = Field(..., alias="thesaurus_term_person")
    predecessor: Union[PersonMeta, None] = Field(..., alias="predecessor")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True



class PersonOut(PersonMeta):
    """Schema for person results."""
    forename_alt_labels: str = Field(alias="forename_alt_labels", example="Johannes ; Jehan")
    surname_alt_labels: str = Field(alias="surname_alt_labels", example="Acciaco de")
    death_date: Union[str, None] = Field(alias="death_date", example="null")
    first_mention_date: Union[str, None] = Field(alias="first_mention_date", example="1356")
    last_mention_date: Union[str, None] = Field(alias="last_mention_date", example="1360")
    is_canon: bool = Field(alias="is_canon", example=True)
    kb_links: List[KbMeta] = Field(alias="related_to")

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class PersonEventsOut(PersonMeta):
    events: List[EventMeta] = Field(alias="events")


class PersonSearchOut(BaseModel):
    """Schema for person search results."""
    query: str = Field(alias="query", example="jean d'acy")
    total: int = Field(alias="total", example=1)
    type_query: str = Field(alias="type_query", example="exact")
    results: List[PersonOut]
