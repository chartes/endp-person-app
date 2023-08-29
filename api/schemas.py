"""
schemas.py

Pydantic models for API endpoints.
Use for validation and serialization.
"""

from typing import Union, List

from pydantic import BaseModel, Field, PrivateAttr


class EventScheme(BaseModel):
    id: int
    type: str
    date: Union[str, None]

    class Config:
        orm_mode = True


class KbLink(BaseModel):
    id: int
    type_kb: str
    url: str

    class Config:
        orm_mode = True


class PersonOut(BaseModel):
    id: int
    id_endp: str = Field(..., alias="_id_endp")
    pref_label: str  # Field("Jean d'Acy", alias="label")
    forename_alt_labels: str
    surname_alt_labels: str
    death_date: Union[str, None]
    first_mention_date: Union[str, None]
    last_mention_date: Union[str, None]
    is_canon: bool
    #kb_links: List[KbLink] = []

    class Config:
        allow_population_by_field_name = True
        orm_mode = True
