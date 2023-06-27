"""
schemas.py

Pydantic models for API endpoints.
Use for validation and serialization.
"""

from typing import Union

from pydantic import BaseModel


class EventScheme(BaseModel):
    id: int
    type: str
    date: Union[str, None]

    class Config:
        orm_mode = True


class PersonScheme(BaseModel):
    id: int
    pref_label: str
    id_endp: str
    # events: list[EventScheme] = []

    class Config:
        orm_mode = True
