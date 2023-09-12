"""
schemas.py

Pydantic models for API endpoints.
Use for validation and serialization.
"""

from typing import Union, List
from enum import Enum

from pydantic import BaseModel, Field

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

# -- Meta schemas --


class BaseMeta(BaseModel):
    """An abstract base class for meta schemas."""
    id_endp: str = Field(alias="_id_endp")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class PersonMeta(BaseMeta):
    """Schema with minimal information on a person."""
    pref_label: str = Field(alias="pref_label")


class ThesaurusMeta(BaseMeta):
    """Schema with minimal information on a thesaurus term."""
    topic: str = Field(alias="topic")
    term: str = Field(alias="term_la")
    term_fr: Union[str, None] = Field(alias="term_fr")
    term_definition: Union[str, None] = Field(alias="definition")


class EventMeta(BaseMeta):
    """Schema with minimal information on an event that concerns a person."""
    date: Union[str, None] = Field(alias="date")
    image_url: Union[str, None] = Field(alias="image_url")
    place_term: Union[ThesaurusMeta, None] = Field(alias="place_term")
    thesaurus_term_person: Union[ThesaurusMeta, None] = Field(alias="thesaurus_term_person")
    predecessor: Union[PersonMeta, None] = Field(alias="predecessor")


class FamilyRelationshipsMeta(BaseMeta):
    """Schema with minimal information on a family relationship that concerns a person."""
    relation_type: str = Field(alias="relation_type")
    relative: Union[PersonMeta, None] = Field(alias="relative")


class KbMeta(BaseMeta):
    """Schema with minimal information on a Knowledge Base link on person."""
    type_kb: str = Field(..., alias="type")
    url: str = Field(..., alias="url")


# -- Out response schemas --

class PersonOut(PersonMeta):
    """Schema with detailed information on a person."""
    forename_alt_labels: str = Field(alias="forename_alt_labels")
    surname_alt_labels: str = Field(alias="surname_alt_labels")
    death_date: Union[str, None] = Field(alias="death_date")
    first_mention_date: Union[str, None] = Field(alias="first_mention_date")
    last_mention_date: Union[str, None] = Field(alias="last_mention_date")
    is_canon: bool = Field(alias="is_canon")
    kb_links: List[KbMeta] = Field(alias="related_to")


class PersonEventsOut(PersonMeta):
    """Schema with detailed information on a person and events that concern them."""
    events: List[EventMeta] = Field(alias="events")


class PersonFamilyRelationshipsOut(PersonMeta):
    """Schema with detailed information on a person and family relationships that concern them."""
    relatives: List[FamilyRelationshipsMeta] = Field(alias="relatives")

# -- Specialized out schemas --


class PersonSearchOut(BaseModel):
    """Schema for person search results."""
    query: str = Field(alias="query")
    total: int = Field(alias="total")
    type_query: str = Field(alias="type_query")
    results: Union[List[PersonOut], None] = Field(alias="results")


class Message(BaseModel):
    """Schema for generic messages."""
    message: str = Field(alias="message")
