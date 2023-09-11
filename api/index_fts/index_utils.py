"""index_utils.py

Whoosh index utils for creating and clearing indexes.
"""
from shutil import rmtree

from whoosh import index


def create_store(store, path) -> None:
    if index.exists_in(path):
        rmtree(path)
    # print(f"Creating store/index in {path}")
    store.destroy()
    store.create()


def create_index(store, schema) -> index:
    store.create_index(schema)


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