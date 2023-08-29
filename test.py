import uuid
import base64
import string
import random

def generate_random_uuid(prefix):
    def replace_punctuation_with_random(string_to_modify):
        punctuation = string.punctuation
        modified_string = ''

        for char in string_to_modify:
            if char in punctuation:
                # Remplacer par un caractère aléatoire majuscule ou minuscule
                random_char = random.choice(string.ascii_letters)
                modified_string += random_char
            else:
                modified_string += char

        return modified_string

    # Générer un UUID
    unique_id = uuid.uuid4()

    # Convertir l'UUID en une chaîne d'octets
    uuid_bytes = unique_id.bytes

    # Encoder les octets en URL-safe Base64
    urlsafe_base64_encoded = base64.urlsafe_b64encode(uuid_bytes)

    # Décoder la chaîne d'octets Base64 en une chaîne Unicode
    urlsafe_base64_encoded_string = urlsafe_base64_encoded.decode('utf-8')

    # Remplacer les ponctuations par des caractères aléatoires
    final_id = replace_punctuation_with_random(urlsafe_base64_encoded_string)

    # ajout du prefixe
    final_id = prefix + final_id

    return final_id

print(generate_random_uuid('per_'))
