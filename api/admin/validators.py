import re
from collections import Counter

from wtforms import ValidationError


def is_valid_kb_links(kb_refs):
    """validate that there is only one link for specific knowledge base"""
    unique_link_required_on = ["Wikidata", "Biblissima", "VIAF", "DataBnF", "Studium Parisiense"]
    type_kb_occurrences = Counter([link.type_kb for link in kb_refs])
    for kb in unique_link_required_on:
        if type_kb_occurrences[kb] > 1:
            raise ValidationError("Vous ne pouvez pas avoir plusieurs liens vers la même base "
                                  "de connaissance pour une personne "
                                  "(Wikidata, Biblissima, VIAF, DataBnF, Studium Parisiense).")


def is_valid_date(_, field):
    """validate that the date is in the correct format"""
    pattern = re.compile(r"^(?:~?\d{4}(?:-(?:0[1-9]|1[0-2])(?:-(?:0[1-9]|1\d|2\d|3[01]))?)?)$")
    if not bool(pattern.match(str(field.data))):
        raise ValidationError(
            "Le format de la date est incorrect."
            " Veuillez utiliser les formats suivants : AAAA-MM-JJ ou AAAA-MM ou AAAA ou"
            " ~AAAA ou ~AAAA-MM ou ~AAAA-MM-JJ (le préfixe '~' désigne une date approximative)"
        )


def is_term_already_exists(result_db, test_term):
    """validate that the term is not already in the database"""
    if result_db is not None:
        raise ValidationError(f"Le terme '{test_term}' est déjà enregistré dans le thesaurus. "
                              f"Voir {result_db.term} ({result_db._id_endp}).")
