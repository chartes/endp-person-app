"""
models.py

SQLAlchemy models for the database
(classes and instances that interact with the database).
"""
import enum
import datetime
from time import time
import uuid
import base64
import string
import random
from functools import wraps

from sqlalchemy import (Column,
                        DateTime,
                        Boolean,
                        ForeignKey,
                        Integer,
                        String,
                        Enum,
                        UniqueConstraint,
                        CheckConstraint,
                        Text,
                        event)
from sqlalchemy.orm import (relationship,
                            backref)

from flask_login import UserMixin
from werkzeug.security import (generate_password_hash,
                               check_password_hash)
import jwt

from .config import settings
from .database import (BASE,
                       session)
from .index_conf import st


# Use sphinx autodoc, uncomment this line and comment relative import
# from sqlalchemy.ext.declarative import declarative_base
# BASE = declarative_base()


def handle_index(method):
    """
    Decorator to handle the index during sqlalchemy events.
    """

    @wraps(method)
    def wrapper(cls, mapper, connection, target):
        """
        Wrapper to handle the index.
        """
        try:
            ix = st.open_index()
            method(cls, mapper, connection, target, ix)
            ix.close()
        except Exception:
            pass

    return wrapper


def generate_random_uuid(prefix: str, provider: str = "") -> str:
    """Generates a random UUID and converts it to a URL-safe Base64 encoded
    bytes string and decoded to a Unicode string.
    """

    def replace_punctuation_with_random(string_to_modify: str) -> str:
        """Replace punctuation characters with random characters."""
        punctuation = string.punctuation
        modified_string = ''

        for char in string_to_modify:
            if char in punctuation:
                # Replace with a random uppercase or lowercase character
                random_char = random.choice(string.ascii_letters)
                modified_string += random_char
            else:
                modified_string += char

        return modified_string

    # Generate a UUID
    unique_id = uuid.uuid4()
    # Convert UUID to bytes
    uuid_bytes = unique_id.bytes
    # Encode the UUID bytes into a bytes string using Base64
    urlsafe_base64_encoded = base64.urlsafe_b64encode(uuid_bytes)
    # Decode the Base64 bytes string into a Unicode string
    urlsafe_base64_encoded_string = urlsafe_base64_encoded.decode('utf-8')
    # replace punctuation with random characters
    # cut uuid to 8 (but possibility to increase or decrease)
    # this represents ≈ 10,376,800,670,380,293 possible identifier combinations
    final_id = replace_punctuation_with_random(urlsafe_base64_encoded_string)[:8]
    # add prefix and provider if exists
    final_id = prefix + "_" + final_id if len(provider) == 0 else prefix + "_" + provider + "_" + final_id
    return final_id


__mapping_prefix__ = {
    "Statut": "term_sts",
    "Dignité": "term_dgn",
    "Ordre sacré": "term_ors",
    "Charge et office": "term_ceo",
    "Chœur": "term_cho",
    "Cloître": "place_cloitre",
    "Prévôté": "place_prevote",
    "Domaine": "place_domaine",
    "Chapelle": "place_chapelle",
    "Entrée": "evt_entree",
    "Sortie": "evt_sortie",
    "Achat d'une maison canoniale": "evt_achat_maison",
    "Choix de la sépulture": "evt_choix_sepulture",
}

__split_name_on_tables__ = ["persons"]


class User(UserMixin, BASE):
    """User model"""
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), index=True, unique=True)
    email = Column(String(120), index=True, unique=True)
    password_hash = Column(String(128))

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        """Set a password hashed"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if password is correct"""
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        """Generate a token for reset password"""
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            settings.FLASK_SECRET_KEY, algorithm='HS256'
        )

    @staticmethod
    def verify_reset_password_token(token):
        """Verify if token is valid"""
        try:
            id_tok = jwt.decode(token,
                                settings.FLASK_SECRET_KEY,
                                algorithms=['HS256'])['reset_password']
        except jwt.exceptions.InvalidTokenError:
            return
        return session.query(User).get(id_tok)

    @staticmethod
    def add_default_user(in_session):
        """Add default user to database"""
        admin = User()
        admin.username = settings.FLASK_ADMIN_NAME
        admin.email = settings.FLASK_ADMIN_MAIL
        admin.password_hash = settings.FLASK_ADMIN_ADMIN_PASSWORD
        in_session.add(admin)
        in_session.commit()


class AbstractActions(BASE):
    __abstract__ = True
    _id_endp = Column(String(25), nullable=False, unique=True)

    @classmethod
    def before_insert_create_id_ref(cls, mapper, connection, target):
        """Generate a forge and random id for the new entry in reference table before insert"""
        is_exist = True
        new_id = None
        try:
            # thesaurus tables specific
            prefix = __mapping_prefix__[target.topic]
        except AttributeError:
            # other tables
            prefix = cls.__prefix__
        # test if new id already exist (not really necessary but just in case)
        if cls.__tablename__:
            while is_exist:
                new_id = generate_random_uuid(prefix=prefix, provider="endp")
                try:
                    if session.query(cls).filter(cls._id_endp == new_id).first() is None:
                        is_exist = False
                    else:
                        print(f"ID already exist: {new_id} in {cls.__tablename__}, retrying...")
                except Exception:
                    is_exist = False
            target._id_endp = new_id

    @classmethod
    def before_insert_get_form_first(cls, mapper, connection, target, separator=";"):
        """Get the first string of a list (separator by default: ";") before insertion."""
        if cls.__tablename__ in __split_name_on_tables__:
            target.forename = target.forename_alt_labels.split(separator)[0]
            target.surname = target.surname_alt_labels.split(separator)[0]

    @classmethod
    @handle_index
    def update_person_fts_index_after_update(cls, mapper, connection, target, ix):
        """Update the index after update a person"""
        if cls.__tablename__ == "persons":
            writer = ix.writer()
            writer.update_document(
                id=str(target.id).encode('utf-8').decode('utf-8'),
                id_endp=str(target._id_endp).encode('utf-8').decode('utf-8'),
                pref_label=str(target.pref_label).encode('utf-8').decode('utf-8'),
                forename_alt_labels=str(target.forename_alt_labels).encode('utf-8').decode('utf-8'),
                surname_alt_labels=str(target.surname_alt_labels).encode('utf-8').decode('utf-8'),
            )
            writer.commit()
            # print(f"Updating Person {target.id} in index")

    @classmethod
    @handle_index
    def insert_person_fts_index_after_insert(cls, mapper, connection, target, ix):
        """Insert a reference in the index"""
        if cls.__tablename__ == "persons":
            writer = ix.writer()
            writer.add_document(
                id=str(target.id).encode('utf-8').decode('utf-8'),
                id_endp=str(target._id_endp).encode('utf-8').decode('utf-8'),
                pref_label=str(target.pref_label).encode('utf-8').decode('utf-8'),
                forename_alt_labels=str(target.forename_alt_labels).encode('utf-8').decode('utf-8'),
                surname_alt_labels=str(target.surname_alt_labels).encode('utf-8').decode('utf-8'),
            )
            writer.commit()
            # print(f"Adding Person {target.id} to index")

    @classmethod
    @handle_index
    def delete_person_fts_index_after_delete(cls, mapper, connection, target, ix):
        """Delete a reference from the index"""
        if cls.__tablename__ == "persons":
            writer = ix.writer()
            writer.delete_by_term('id', str(target.id))
            writer.commit()
            # print(f"Deleting Person {target.id} from index")


# Attach event listeners to AbstractActions class for insert/update/delete events
@event.listens_for(AbstractActions, "before_insert", propagate=True)
def before_insert(mapper, connection, target):
    """Methods called before insertion in database"""
    target.before_insert_create_id_ref(mapper, connection, target)
    target.before_insert_get_form_first(mapper, connection, target)


@event.listens_for(AbstractActions, "after_insert", propagate=True)
def after_insert(mapper, connection, target):
    """Methods called after insertion in database"""
    target.insert_person_fts_index_after_insert(mapper, connection, target)


@event.listens_for(AbstractActions, "after_update", propagate=True)
def after_update(mapper, connection, target):
    """Methods called after update in database"""
    target.update_person_fts_index_after_update(mapper, connection, target)


@event.listens_for(AbstractActions, "after_delete", propagate=True)
def after_delete(mapper, connection, target):
    """Methods called after deletion in database"""
    target.delete_person_fts_index_after_delete(mapper, connection, target)


# ~~~~~~~~~~~~~~~~~~~ > Enum classes < ~~~~~~~~~~~~~~~~~~~


class KnowledgeBaseLabels(enum.Enum):
    """Liste contrôlée des bases de connaissances.

    :param WIKIDATA: Wikidata (https://www.wikidata.org/)
    :param BIBLISSIMA: Biblissima (https://portail.biblissima.fr/)
    :param VIAF: VIAF (https://viaf.org/)
    :param DATABNF: DataBnF (https://data.bnf.fr/)
    :param STUDIUM: Studium Parisiense (http://studium-parisiense.univ-paris1.fr/)
    :param COLLECTA: Collecta (http://www.collecta.fr/)
    """
    __order__ = "WIKIDATA BIBLISSIMA VIAF DATABNF STUDIUM COLLECTA"
    WIKIDATA = "Wikidata"
    BIBLISSIMA = "Biblissima"
    VIAF = "VIAF"
    DATABNF = "DataBnF"
    STUDIUM = "Studium Parisiense"
    COLLECTA = "Collecta"

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


class EventTypeLabels(enum.Enum):
    """Liste contrôlée des types d'événements connus pour une personne.

    :param ENTREE: Motif d'entrée de charge pour une personne (par exemple, élection, collation, installation) ; spécifications supplémentaires dans un champ commentaire.
    :param SORTIE: Motif de sortie de charge pour une personne (par exemple expulsion, renonciation, permutation, mort) ; spécifications supplémentaires dans un champ commentaire.
    :param ACHAT_MAISON:  Achat d'une maison canoniale.
    :param CHOIX_SEPULTURE: Choix de la sépulture.
    """
    __order__ = "ENTREE SORTIE ACHAT_MAISON CHOIX_SEPULTURE"
    # motif d'entrée :
    ENTREE = "Entrée"  # Désignation = toutes les entrées de charges pour le chapitre (chanoines et autres) - saisie comp. dans un champ commentaire libre.
    # election = "Élection"                      # Élection à une charge par le chapitre.
    # collation = "Collation"                    # Octroi du bénéfice et/ou de la prébende et/ou de la charge.
    # installation = "Installation"              # Prise de poste pour un chanoine.
    # designation = "Désignation"                # Désignation/Engagement à une charge ou une chapelle (Cf. persons_perform_religious_services_in)

    # motif de sortie de charge :
    SORTIE = "Sortie"
    # expulsion = "expulsion"                 # expulsion, licenciement
    # resignacio = "Resignacio, Renunciacio"  # renonciation
    # permutacio = "Permutacio"               # permutation
    # mort = "Mort"                           # mort
    ACHAT_MAISON = "Achat d'une maison canoniale"  # Achat d'une maison canoniale.
    CHOIX_SEPULTURE = "Choix de la sépulture"  # ...

    def __repr__(self):
        return self.value

    def __str__(self):
        return self.value


class FamilyRelationshipLabels(enum.Enum):
    """Liste contrôlée des types de relations familiales.

    :param IS_SON_OF:      fils de
    :param IS_DAUGHTER_OF: fille de
    :param IS_SPOUSE:      conjoint(e) de
    :param IS_FATHER_OF:   père de
    :param IS_MOTHER_OF:   mère de
    :param IS_NEPHEW_OF:   neveu de
    :param IS_NIECE_OF:    nièce de
    :param IS_UNCLE_OF:    oncle de
    :param IS_AUNT_OF:     tante de
    :param IS_BROTHER_OF:  frère de
    :param IS_SISTER_OF:   sœur de
    :param IS_FAMILIAR_OF: familier de

    """
    __order__ = "IS_SON_OF IS_DAUGHTER_OF IS_SPOUSE IS_FATHER_OF IS_MOTHER_OF IS_NEPHEW_OF IS_NIECE_OF IS_UNCLE_OF IS_AUNT_OF IS_BROTHER_OF IS_SISTER_OF IS_FAMILIAR_OF"
    IS_SON_OF = "fils de"
    IS_DAUGHTER_OF = "fille de"
    IS_SPOUSE = "conjoint(e) de"
    IS_FATHER_OF = "père de"
    IS_MOTHER_OF = "mère de"
    IS_NEPHEW_OF = "neveu de"
    IS_NIECE_OF = "nièce de"
    IS_UNCLE_OF = "oncle de"
    IS_AUNT_OF = "tante de"
    IS_BROTHER_OF = "frère de"
    IS_SISTER_OF = "sœur de"
    IS_FAMILIAR_OF = "familier de"

    def __repr__(self):
        return self.value

    def __str__(self):
        return self.value


class ThesaurusTopicLabels(enum.Enum):
    """Liste contrôlée des topics pour les thesauri qui s'applique aux personnes.

    :param STATUTS:  Statuts
    :param DIGNITES: Dignités
    :param ORDRES_SACRES: Ordres sacrés
    :param CHARGES_OFFICES: Charges et offices
    :param CHOEUR: Choeur
    """
    __order__ = "STATUT DIGNITE ORDRE_SACRE CHARGE_OFFICE CHOEUR"
    STATUT = "Statut"
    DIGNITE = "Dignité"
    ORDRE_SACRE = "Ordre sacré"
    CHARGE_OFFICE = "Charge et office"
    CHOEUR = "Chœur"

    def __repr__(self):
        return self.value

    def __str__(self):
        return self.value


class ThesaurusPlacesTopicsLabels(enum.Enum):
    """Liste contrôlée des topics pour les thesauri qui s'applique aux lieux.

    :param CLOITRE: Cloître
    :param PREVOTE: Prévôté
    :param DOMAINE: Domaine
    :param CHAPELLE: Chapelle
    """
    __order__ = "CLOITRE PREVOTE DOMAINE CHAPELLE"
    CLOITRE = "Cloître"
    PREVOTE = "Prévôté"
    DOMAINE = "Domaine"
    CHAPELLE = "Chapelle"

    def __repr__(self):
        return self.value

    def __str__(self):
        return self.value


def _get_enum_values(enum_class):
    return (item.value for item in enum_class)


###########################################################
# ~~~~~~~~~~~~~~~~~~~ > Main tables < ~~~~~~~~~~~~~~~~~~~


class Person(AbstractActions):
    """Personnes (chanoines & Cie) relevées et identifiées dans les registres de Notre-Dame de Paris.


    :param id: Clé primaire autoincrémentée. [REQ.]
    :type id: PRIMARY_KEY
    :param _id_endp: Identifiant forgé dans la base (avec préfixe per\_). [REQ.]
    :type _id_endp: STRING(25)
    :param pref_label: Libellé préférentiel normalisé de la personne. [REQ.]
    :type pref_label: STRING(125)
    :param forename: Prénom préférentiel (nomen). [REQ.]
    :type forename: STRING(45)
    :param forename_alt_labels: Formes alternatives du prénom (nomen). [REQ.]
    :type forename_alt_labels: STRING(100)
    :param surname: Nom de famille préférentiel (cognomen - patronyme). [REQ.]
    :type surname: STRING(45)
    :param surname_alt_labels: Formes alternatives du nom de famille (cognomen - patronyme). [REQ.]
    :type surname_alt_labels: STRING(100)
    :param first_mention_date: Année de la première mention de la personne dans les registres (sous la forme YYYY ou ~YYYY si approximatif). [REQ.]
    :type first_mention_date: STRING(25)
    :param last_mention_date: Année de la dernière mention de la personne dans les registres (sous la forme YYYY ou ~YYYY si approximatif). [REQ.]
    :type last_mention_date: STRING(25)
    :param death_date: Date de décès (YYYY, ou YYYY-MM ou YYYY-MM-DD) [OPT.]
    :type death_date: STRING(25)
    :param is_canon: chanoine (1) ou non chanoine (0) [REQ.]
    :type is_canon: BOOLEAN
    :param comment: Commentaire libre. [OPT.]
    :type comment: TEXT
    :param bibliography: Bibliographie. [OPT.]
    :type bibliography: TEXT
    :param _created_at: Date de création de la fiche. [REQ.]
    :type _created_at: DATE
    :param _updated_at: Date de mise à jour de la fiche. [REQ.]
    :type _updated_at: DATE
    :param _last_editor: Dernier éditeur de la fiche. [REQ.]
    :type _last_editor: STRING(25)
    """
    __tablename__ = "persons"
    __prefix__ = "person"
    info = {'use_fts5': True}
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    pref_label = Column(String(125), nullable=False, unique=False)
    forename = Column(String(45), nullable=False, unique=False)
    forename_alt_labels = Column(String(100), nullable=False, unique=False)
    surname = Column(String(45), nullable=False, unique=False)
    surname_alt_labels = Column(String(100), nullable=False, unique=False)
    first_mention_date = Column(String(25), nullable=True, unique=False)
    last_mention_date = Column(String(25), nullable=True, unique=False)
    death_date = Column(String(25), nullable=True, unique=False)
    is_canon = Column(Boolean, nullable=False, unique=False, default=False)
    comment = Column(Text, nullable=True, unique=False)
    bibliography = Column(Text, nullable=True, unique=False)

    events = relationship("Event",
                          foreign_keys="Event.person_id",
                          cascade="all, delete-orphan",
                          order_by="Event.date.asc()",
                          lazy="dynamic",
                          back_populates="person")
    _events_predecessors = relationship("Event",
                                        foreign_keys="Event.predecessor_id", )
    kb_links = relationship("PersonHasKbLinks",
                            foreign_keys="PersonHasKbLinks.person_id",
                            cascade="all, delete, delete-orphan",
                            # lazy="dynamic",
                            back_populates="person")
    family_links = relationship("PersonHasFamilyRelationshipType",
                                back_populates="person",
                                cascade="all, delete, delete-orphan",
                                foreign_keys="PersonHasFamilyRelationshipType.person_id")
    family_links_relative = relationship("PersonHasFamilyRelationshipType",
                                         back_populates="relative",
                                         foreign_keys="PersonHasFamilyRelationshipType.relative_id",
                                         cascade="all, delete, delete-orphan")
    _created_at = Column(DateTime, default=datetime.datetime.now())
    _updated_at = Column(DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())
    _last_editor = Column(String(25), nullable=True, unique=False)

    def __repr__(self):
        return f"<Personne : {self.id} | {self.pref_label} (mort : {self.death_date})>"


###########################################################
# ~~~~~~~~~~~~~~~~~~~ > Referential tables < ~~~~~~~~~~~~~~~~~~~
# > Abstract Referential Classes


class AbstractGenericThesaurusTerm(AbstractActions):
    """Classe abstraite pour représenter un thesaurus"""
    __abstract__ = True

    __prefix__ = ""

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    term = Column(String(200), nullable=False, unique=False)
    term_fr = Column(String(200), nullable=True, unique=False)
    term_definition = Column(Text, nullable=True, unique=False)
    term_position = Column(String(200), nullable=True, unique=False)

    def __repr__(self):
        return f"<{self.topic} : {self.id} | {self.term} ({self.term_fr})>"


class Event(AbstractActions):
    """Liste d'événements pouvant survenir dans le parcours d'une personne:

    Les types d'événements sont les suivants :
        - Entrée
        - Sortie
        - Achat d'une maison canoniale
        - Choix de la sépulture

    Cf. :class:`EventTypeLabels`

    :param id: Clé primaire autoincrémentée. [REQ.]
    :type id: PRIMARY_KEY
    :param _id_endp: Identifiant forgé dans la base avec le préfixe correspondant :

        - Entrée                         : evt_entree\_,
        - Sortie                         : evt_sortie\_,
        - Achat d'une maison canoniale   : evt_achat_maison\_,
        - Choix de la sépulture          : evt_choix_sepulture\_ [REQ.]

    :type _id_endp: STRING(25)
    :param type: Type d'événement (Cf. :class:`EventTypeLabels`).  [REQ.]
    :type type: ENUM(EventTypeLabels)
    :param person_id: Identifiant de la personne concerné par l'événement. [REQ.]
    :type person_id: FOREIGN_KEY(Person)
    :param date: date de l'événement (YYYY, YYYY-MM, ou YYYY-MM-DD) [OPT.]
    :type date: STRING(25)
    :param image_url: URL de l'image du registre. [OPT.]
    :type image_url: STRING(25)
    :param place_term_id: Identifiant du lieu lié à l'événement. [OPT.]
    :type place_term_id: FOREIGN_KEY(PlacesTerm)
    :param person_thesaurus_term_id: Identifiant du terme du thesaurus pour une personne (statuts, charges & offices, choeur et dignités) lié à l'évenement. [OPT.]
    :type person_thesaurus_term_id: FOREIGN_KEY(ThesaurusTerm)
    :param predecessor_id: Identifiant de la personne précédente (pour les permutacio par exemple)  [OPT.]
    :type predecessor_id: FOREIGN_KEY(Person)
    :param comment: Commentaire libre. [OPT.]
    :type comment: TEXT
    """
    __tablename__ = "events"
    __prefix__ = "event"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    type = Column(Enum(*_get_enum_values(EventTypeLabels)), nullable=False, unique=False)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False, unique=False)
    date = Column(String(25), nullable=True, unique=False)
    image_url = Column(Text(), nullable=True, unique=False)
    place_term_id = Column(Integer, ForeignKey("places_thesaurus_terms.id", onupdate="CASCADE", ondelete="CASCADE"),
                           nullable=True, unique=False)
    person_thesaurus_term_id = Column(Integer,
                                      ForeignKey("persons_thesaurus_terms.id", onupdate="CASCADE", ondelete="CASCADE"),
                                      nullable=True, unique=False)
    predecessor_id = Column(Integer, ForeignKey("persons.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True,
                            unique=False)
    comment = Column(Text, nullable=True, unique=False)

    person = relationship("Person",
                          foreign_keys="Event.person_id",
                          back_populates="events")
    predecessor = relationship("Person",
                               foreign_keys=[predecessor_id],
                               back_populates="_events_predecessors")

    place_term = relationship("PlacesTerm",
                              backref=backref('events', cascade="all, delete"), )

    thesaurus_term_person = relationship("ThesaurusTerm",
                                         backref=backref('events', cascade="all, delete"), )

    def __repr__(self):
        return f"<Event: {self._id_endp} | {self.type} | {self.person_id} | {self.date} | {self.place_term_id} | {self.person_thesaurus_term_id} | {self.predecessor_id} | {self.comment}>"


# > Referential Classes about people


class ThesaurusTerm(AbstractGenericThesaurusTerm):
    """Thesaurus pour les personnes.

    Les topics sont les suivants :
        - Status
        - Dignités
        - Ordres sacrés
        - Charges et offices
        - Chœur

    Cf. :class:`ThesaurusTopicLabels`

    :param id: Clé primaire autoincrémentée. [REQ.]
    :type id: PRIMARY_KEY
    :param _id_endp: Identifiant forgé dans la base avec le préfixe correspondant :

        - Statuts            : term_sts\_,
        - Dignités           : term_dgn\_,
        - Ordres sacrés      : term_ors\_,
        - Charges et offices : term_ceo\_,
        - Choeur             : term_cho\_ [REQ.]

    :type _id_endp: STRING(25)
    :param topic: Topic du thesaurus [REQ.]
    :type topic: ENUM(ThesaurusTopicLabels)
    :param term: prefLabel. [REQ.]
    :type term: STRING(125)
    :param term_fr: prefLabel en français. [OPT.]
    :type term_fr: STRING(25)
    :param term_definition: Définition. [OPT.]
    :type term_definition: TEXT
    :param term_position: Numéro d'ordre. [IMPLEMENT BUT NOT REQUIRED - OPT.]
    :type term_position: STRING(125)

    """
    __tablename__ = "persons_thesaurus_terms"
    __prefix__ = "person_th_term"
    __display_name__ = "Thesaurus de termes pour les personnes"
    # Clé de regroupement
    topic = Column(Enum(*_get_enum_values(ThesaurusTopicLabels)), nullable=False, unique=False)


# > Referential Classes about places


class PlacesTerm(AbstractGenericThesaurusTerm):
    """Thesaurus pour les lieux.

    Les topics sont les suivants :
        - Cloîtres
        - Prévôtés
        - Domaines
        - Chapelles

    Cf. :class:`ThesaurusPlacesTopicsLabels`

    :param id: Clé primaire autoincrémentée. [REQ.]
    :type id: PRIMARY_KEY
    :param _id_endp: Identifiant forgé dans la base avec le préfixe correspondant :

        - Cloîtres         : place_cloitre\_,
        - Prévôtés         : place_prevote\_,
        - Domaines         : place_domaine\_,
        - Chapelles [REQ.] : place_chapelle\_

    :param term:  prefLabel. [REQ.]
    :type term: STRING(25)
    :param term_fr: prefLabel en français. [OPT.]
    :type term_fr: STRING(25)
    :param term_definition: Définition. [OPT.]
    :type term_definition: TEXT
    :param term_position: Numéro d'ordre [IMPLEMENT BUT NOT REQUIRED - OPT.].
    :type term_position: STRING(125)
    :param topic: Topic du thesaurus de lieux [REQ.]
    :type topic: ENUM(ThesaurusPlacesTopicsLabels)
    """
    __tablename__ = "places_thesaurus_terms"
    __prefix__ = "place_th_term"
    __display_name__ = "Thesaurus de lieux"
    # Clé de regroupement
    topic = Column(Enum(*_get_enum_values(ThesaurusPlacesTopicsLabels)), nullable=False, unique=False)

    # Expérimentations avec données du map
    map_chap_nomenclature_id = Column(String, nullable=False, unique=False)
    map_chap_label_new = Column(String, nullable=False, unique=False)
    map_chap_label_old = Column(String, nullable=False, unique=False)
    map_chap_before_restore_url = Column(String, nullable=False, unique=False)
    map_chap_after_restore_url = Column(String, nullable=False, unique=False)



# ~~~~~~~~~~~~~~~~~~~ > Association tables < ~~~~~~~~~~~~~~~~~~~


class PersonHasFamilyRelationshipType(AbstractActions):
    """Une personne peut avoir 1 ou plusieurs relations familiales.

    :param id: Clé primaire autoincrémentée. [REQ.]
    :type id: PRIMARY_KEY
    :param person_id: Identifiant de la personne. [REQ.]
    :type person_id: FOREIGN_KEY(Person)
    :param relative_id: Identifiant de la personne avec laquelle on associe une relation familiale. [REQ.]
    :type relative_id: FOREIGN_KEY(Person)
    :param relation_type: Type de relation familiale. [REQ.]
    :type relation_type: ENUM(FamilyRelationshipLabels)
    """
    __tablename__ = "person_has_family_relationships_type"
    __prefix__ = "family_relationship"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    __table_args__ = (
        UniqueConstraint('person_id', 'relative_id', name="_person_has_family_relationships_type"),
        CheckConstraint('person_id != relative_id', name="_no_circular_relationship"),
    )

    person_id = Column(Integer, ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, unique=False)
    relative_id = Column(Integer, ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, unique=False)

    relation_type = Column(Enum(*_get_enum_values(FamilyRelationshipLabels)), nullable=False, unique=False)

    person = relationship("Person", foreign_keys=[person_id], uselist=False)
    relative = relationship("Person", foreign_keys=[relative_id], uselist=False)


class PersonHasKbLinks(AbstractActions):
    """Une personne peut avoir 1 ou plusieurs liens vers des bases de connaissances

    :param id: Clé primaire autoincrémentée. [REQ.]
    :type id: PRIMARY_KEY
    :param person_id: Identifiant de la personne à lier. [REQ.]
    :type person_id: FOREIGN_KEY(Person)
    :param type_kb: Type de relation familiale. [REQ.]
    :type type_kb: ENUM(KnowledgeBaseLabels)
    :param url: Url vers la base de connaissance. [REQ.]
    :type url: STRING(200)
    """
    __tablename__ = "person_has_kb_links"
    __prefix__ = "person_kb"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    person_id = Column(Integer, ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, unique=False)
    type_kb = Column(Enum(*_get_enum_values(KnowledgeBaseLabels)), nullable=False, unique=False)
    url = Column(String(200), nullable=False, unique=False)

    person = relationship("Person", back_populates="kb_links")

    def __repr__(self):
        return f"<PersonHasKbLinks: {self.person_id} | {self.type_kb} | {self.url}>"
