import re
from collections import Counter

import requests
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
def is_custom_date_format(value):
    pattern = r"^(?:~?\d{4}(?:-(?:0[1-9]|1[0-2])(?:-(?:0[1-9]|1\d|2\d|3[01]))?)?)$"
    return bool(re.match(pattern, value))

def is_valid_date(_, field):
    """validate that the date is in the correct format"""
    if not is_custom_date_format(str(field.data)):
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


def is_family_link_circular(result_db):
    """validate that the family link is not circular"""
    for result in result_db:
        if result.relative.id == result.person.id:
            raise ValidationError(f"Vous ne pouvez pas créer un lien familial entre une personne et elle-même. "
                                  f"Circularité: {result.person.pref_label} {result.relation_type} {result.relative.pref_label}.")


def is_family_link_valid(result_db):
    """validate that the family relationship between 1 and 1"""
    check = Counter([(res.person.id, res.relative.id, res.person.pref_label, res.relative.pref_label) for res in result_db])
    for k, v in check.items():
        if v > 1:
            raise ValidationError(f"Vous ne pouvez pas créer plusieurs liens familiaux entre la personne {k[2]} et la personne {k[3]}.")


def is_nakala_image_valid(_, field):
    """validate that the image is a nakala image"""
    if not ';' in field.data:
        raise ValidationError(f"L'image de l'événement doit contenir un séparateur ';' entre la cote du registre et le nom de l'image.")
    test_value = field.data.split(';')
    if len(test_value) != 2:
        raise ValidationError(f"L'image de l'événement doit exclusivement contenir la cote du registre et le nom de l'image, n'essayez pas d'ajouter le SHA1.")
    if not test_value[0].strip().startswith('LL'):
        raise ValidationError(f"La cote du registre doit commencer par 'LL'.")
    if not test_value[1].strip().startswith('FRAN'):
        raise ValidationError(f"Le nom de l'image doit commencer par 'FRAN_'.")

