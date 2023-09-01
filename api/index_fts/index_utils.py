"""index_utils.py

Whoosh index utils for creating and clearing indexes.
"""
import os
from shutil import rmtree

from whoosh import index


from api.index_fts.schemas import PersonIdxSchema

SCHEMAS = [PersonIdxSchema]


def clear_index(index_dir):
    if os.path.exists(index_dir):
        rmtree(index_dir)


def create_index(index_dir):
    clear_index(index_dir)
    index_ = None
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)
    for schema in SCHEMAS:
        index_ = index.create_in(index_dir, schema)
    return index_


def populate_index(session, index_, model):
    persons = session.query(model).all()
    writer = index_.writer()
    for person in persons:
        writer.add_document(
            id=str(person.id),
            id_endp=person._id_endp,
            pref_label=person.pref_label.strip().lower(),
            forename_alt_labels=person.forename_alt_labels.strip().lower(),
            surname_alt_labels=person.surname_alt_labels.strip().lower()
        )
    writer.commit()
    return index_