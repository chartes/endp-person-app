"""schemas.py

Whoosh schemas for index and full-text search.
"""

from whoosh.fields import (SchemaClass,
                           ID,
                           TEXT)


class PersonIdxSchema(SchemaClass):
    """Schema for the PersonIdx index."""
    id = ID(stored=True, unique=True)
    id_endp = TEXT(stored=True)
    pref_label = TEXT(stored=True)
    forename_alt_labels = TEXT(stored=True)
    surname_alt_labels = TEXT(stored=True)