import re

from wtforms import ValidationError


def is_valid_date(form, field):
    pattern = re.compile(r"^(?:~?\d{4}(?:-(?:0[1-9]|1[0-2])(?:-(?:0[1-9]|1\d|2\d|3[01]))?)?)$")
    if not bool(pattern.match(str(field.data))):
        raise ValidationError(
            'Le format de la date est incorrect. Veuillez utiliser les formats suivants : AAAA-MM-JJ ou AAAA-MM ou AAAA ou ~AAAA ou ~AAAA-MM ou ~AAAA-MM-JJ (date approximative)')


def is_separated_by_semicolons(form, field):
    pattern = re.compile(r"^(?!\s*;\s*)(\s*\S+\s*;\s*)*\s*\S+\s*$")
    if not bool(pattern.match(str(field.data))):
        raise ValidationError(
            'Les valeurs multiples doivent être séparées par des points-virgules, par exemple : valeur1; valeur2; valeur3')