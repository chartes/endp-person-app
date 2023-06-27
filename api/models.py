"""
models.py

SQLAlchemy models for the database
(classes and instances that interact with the database).
"""
import enum
import datetime

from sqlalchemy import (Column,
                        DateTime,
                        Boolean,
                        ForeignKey,
                        Integer,
                        String,
                        Enum,
                        UniqueConstraint,
                        Text,
                        event)
from sqlalchemy.orm import (relationship)
from sqlalchemy import text
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .database import BASE, session


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
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), index=True, unique=True)
    email = Column(String(120), index=True, unique=True)
    password_hash = Column(String(128))

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def add_default_user():
        """Ajoute un utilisateur par défaut"""
        admin = User()
        admin.username = "admin"
        admin.email = "admin.endp@chartes.psl.eu"
        admin.password_hash = "pbkdf2:sha256:600000$gpxiSgaDAtJwVELW$eb" \
                              "1061add8fc1b27ed8b337ce6b29766c2c9c0f6303" \
                              "92429d57382f5570ac207"
        session.add(admin)



class AbstractActions(BASE):
    __abstract__ = True
    _id_endp = Column(String(25), nullable=False, unique=True)

    @classmethod
    def before_insert_create_id_ref(cls, mapper, connection, target):
        """Génère l'ID forgé de référentiel avant l'insertion"""
        # retourne le bon prefixe pour forgé l'id_reference
        # prefix = None
        try:
            prefix = __mapping_prefix__[target.topic]
        except AttributeError:
            prefix = cls.__prefix__
        # Récupérer l'id_reference du dernier enregistrement
        try:
            new_id = session.query(cls).filter(cls.topic == target.topic).order_by(cls.id).all()[-1]._id_endp
            new_id = int(new_id.split("_")[-1]) + 1
            # Générer l'ID de référentiel basé sur le nombre de lignes existantes
            target._id_endp = f"{prefix}_{new_id}"
        #print(f"test: {[t for t in test]}")
        except:
            count = connection.scalar(text(f"SELECT _id_endp FROM {cls.__tablename__} ORDER BY id DESC LIMIT 1"))
            if count is None:
                # Récupérer le nombre de lignes existantes
                count = connection.scalar(text(f"SELECT COUNT(*) FROM {cls.__tablename__}"))
            else:
                count = int(count.split("_")[-1])
                # Générer l'ID de référentiel basé sur le nombre de lignes existantes
            target._id_endp = f"{prefix}_{count + 1}"

        #connection.close()

    @classmethod
    def before_insert_get_form_first(cls, mapper, connection, target, separator=";"):
        """Récupère la première chaîne de caractère d'une liste (séparateur par défaut: ";") avant l'insertion"""
        if cls.__tablename__ in __split_name_on_tables__:
            target.forename = target.forename_alt_labels.split(separator)[0]
            target.surname = target.surname_alt_labels.split(separator)[0]


@event.listens_for(AbstractActions, "before_insert", propagate=True)
def before_insert(mapper, connection, target):
    """Méthodes appelées avant l'insertion dans la base de données"""
    target.before_insert_create_id_ref(mapper, connection, target)
    target.before_insert_get_form_first(mapper, connection, target)

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
    __order__     = "WIKIDATA BIBLISSIMA VIAF DATABNF STUDIUM COLLECTA"
    WIKIDATA      = "Wikidata"
    BIBLISSIMA    = "Biblissima"
    VIAF          = "VIAF"
    DATABNF       = "DataBnF"
    STUDIUM       = "Studium Parisiense"
    COLLECTA      = "Collecta"

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
    __order__       = "ENTREE SORTIE ACHAT_MAISON CHOIX_SEPULTURE"
    # motif d'entrée :
    ENTREE          = "Entrée"  # Désignation = toutes les entrées de charges pour le chapitre (chanoines et autres) - saisie comp. dans un champ commentaire libre.
    # election = "Élection"                      # Élection à une charge par le chapitre.
    # collation = "Collation"                    # Octroi du bénéfice et/ou de la prébende et/ou de la charge.
    # installation = "Installation"              # Prise de poste pour un chanoine.
    # designation = "Désignation"                # Désignation/Engagement à une charge ou une chapelle (Cf. persons_perform_religious_services_in)

    # motif de sortie de charge :
    SORTIE          = "Sortie"
    # expulsion = "expulsion"                 # expulsion, licenciement
    # resignacio = "Resignacio, Renunciacio"  # renonciation
    # permutacio = "Permutacio"               # permutation
    # mort = "Mort"                           # mort
    ACHAT_MAISON    = "Achat d'une maison canoniale"    # Achat d'une maison canoniale.
    CHOIX_SEPULTURE = "Choix de la sépulture"        # ...

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
    __order__      = "IS_SON_OF IS_DAUGHTER_OF IS_SPOUSE IS_FATHER_OF IS_MOTHER_OF IS_NEPHEW_OF IS_NIECE_OF IS_UNCLE_OF IS_AUNT_OF IS_BROTHER_OF IS_SISTER_OF IS_FAMILIAR_OF"
    IS_SON_OF      = "fils de"
    IS_DAUGHTER_OF = "fille de"
    IS_SPOUSE      = "conjoint(e) de"
    IS_FATHER_OF   = "père de"
    IS_MOTHER_OF   = "mère de"
    IS_NEPHEW_OF   = "neveu de"
    IS_NIECE_OF    = "nièce de"
    IS_UNCLE_OF    = "oncle de"
    IS_AUNT_OF     = "tante de"
    IS_BROTHER_OF  = "frère de"
    IS_SISTER_OF   = "sœur de"
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
    __order__       = "STATUT DIGNITE ORDRE_SACRE CHARGE_OFFICE CHOEUR"
    STATUT         = "Statut"
    DIGNITE        = "Dignité"
    ORDRE_SACRE   = "Ordre sacré"
    CHARGE_OFFICE = "Charge et office"
    CHOEUR          = "Chœur"

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
    __order__       = "CLOITRE PREVOTE DOMAINE CHAPELLE"
    CLOITRE         = "Cloître"
    PREVOTE         = "Prévôté"
    DOMAINE         = "Domaine"
    CHAPELLE        = "Chapelle"

    def __repr__(self):
        return self.value

    def __str__(self):
        return self.value


def _get_enum_values(enum_class):
    return (item.value for item in enum_class)


#THESAURUS_TOPIC_LABELS = (topic.value for topic in ThesaurusTopicLabels)
#THESAURUS_PLACES_TOPIC_LABELS = (topic.value for topic in ThesaurusPlacesTopicsLabels)


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

    events       = relationship("Event", back_populates="person", foreign_keys="Event.person_id", cascade="all, delete-orphan")
    kb_links     = relationship("PersonHasKbLinks", back_populates="person", foreign_keys="PersonHasKbLinks.person_id")
    family_links = relationship("PersonHasFamilyRelationshipType", back_populates="person", foreign_keys="PersonHasFamilyRelationshipType.person_id")

    _created_at  = Column(DateTime, default=datetime.datetime.now())
    _updated_at  = Column(DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())
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
    term = Column(String(125), nullable=False, unique=False)
    term_fr = Column(String(25), nullable=True, unique=False)
    term_definition = Column(Text, nullable=True, unique=False)
    term_position = Column(String(125), nullable=True, unique=False)

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
    image_url = Column(String(25), nullable=True, unique=False)
    place_term_id = Column(Integer, ForeignKey("places_thesaurus_terms.id"), nullable=True, unique=False)
    person_thesaurus_term_id = Column(Integer, ForeignKey("persons_thesaurus_terms.id"), nullable=True, unique=False)
    predecessor_id = Column(Integer, ForeignKey("persons.id"), nullable=True, unique=False)
    comment = Column(Text, nullable=True, unique=False)

    person = relationship("Person", back_populates="events", foreign_keys="Event.person_id")
    place_term = relationship("PlacesTerm", foreign_keys=[place_term_id])
    thesaurus_term_person = relationship("ThesaurusTerm", foreign_keys=[person_thesaurus_term_id])

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
    :param term_position: Numéro d'ordre. [OPT.]
    :type term_position: STRING(125)

    """
    __tablename__ = "persons_thesaurus_terms"
    __prefix__ = "person_th_term"
    __display_name__ = "Thesaurus de termes pour les personnes"
    # Clé de regroupement
    topic = Column(Enum(*_get_enum_values(ThesaurusTopicLabels)), nullable=False, unique=False)

    # when term is delete remove all events with this term
    events = relationship("Event", back_populates="thesaurus_term_person", cascade="all, delete-orphan", foreign_keys="Event.person_thesaurus_term_id")

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
    :param term_position: Numéro d'ordre [OPT.].
    :type term_position: STRING(125)
    :param topic: Topic du thesaurus de lieux [REQ.]
    :type topic: ENUM(ThesaurusPlacesTopicsLabels)
    """
    __tablename__ = "places_thesaurus_terms"
    __prefix__ = "place_th_term"
    __display_name__ = "Thesaurus de lieux"
    # Clé de regroupement
    topic = Column(Enum(*_get_enum_values(ThesaurusPlacesTopicsLabels)), nullable=False, unique=False)

    # when term is delete remove all events with this term
    events = relationship("Event", back_populates="place_term", cascade="all, delete-orphan", foreign_keys="Event.place_term_id")
# ~~~~~~~~~~~~~~~~~~~ > Association tables < ~~~~~~~~~~~~~~~~~~~

class PersonHasFamilyRelationshipType(BASE):
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
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    __table_args__ = (UniqueConstraint('person_id', 'relative_id', name="_person_has_family_relationships_type"),)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False, unique=False)
    relative_id = Column(Integer, ForeignKey("persons.id"), nullable=False, unique=False)
    relation_type = Column(Enum(*_get_enum_values(FamilyRelationshipLabels)), nullable=False, unique=False)

    person = relationship("Person", foreign_keys=[person_id])
    relative = relationship("Person", foreign_keys=[relative_id])


class PersonHasKbLinks(BASE):
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
    __prefix__ = "per_kb"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    person_id = Column(Integer, ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, unique=False)
    type_kb = Column(Enum(*_get_enum_values(KnowledgeBaseLabels)), nullable=False, unique=False)
    url = Column(String(200), nullable=False, unique=False)

    person = relationship("Person", back_populates="kb_links")

    def __repr__(self):
        return f"<PersonHasKbLinks: {self.person_id} | {self.type_kb} | {self.url}>"
