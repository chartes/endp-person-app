"""
views.py

Model views for the admin interface.
"""
import json

from flask import (redirect,
                   url_for,
                   flash,
                   jsonify,
                   request)
from flask_admin.contrib.sqla import ModelView
from flask_admin import (BaseView,
                         expose,
                         AdminIndexView)
from flask_login import (current_user,
                         logout_user,
                         login_user)
from wtforms.fields import PasswordField
from sqlalchemy import and_, or_

from ..models import (Event,
                      User,
                      Person,
                      PersonHasKbLinks,
                      PersonHasFamilyRelationshipType,
                      PlacesTerm,
                      ThesaurusTerm)
from ..database import session
from ..crud import (get_person,
                    get_thesaurus_term,
                    get_thesaurus_terms,
                    get_user,
                    get_events)
from .forms import LoginForm
from .formaters import (_markup_interpret,
                        _bold_item_list,
                        _color_on_bool,
                        _dateformat,
                        _hyperlink_item_list,
                        _format_label_form_with_tooltip,
                        _thumbnail_interpret, )
from .validators import (is_valid_date,
                         is_valid_kb_links,
                         is_term_already_exists,
                         is_family_link_circular,
                         is_family_link_valid)
from .widgets import (Select2DynamicWidget,
                      Select2NakalaChoicesWidget)
from .constants import (NAKALA_IMAGES,
                        NAKALA_DATA_IDENTIFIERS)

EDIT_ENDPOINTS = ["person", "placesterm", "thesaurusterm"]
can_edit_roles = ['ADMIN', 'EDITOR', 'CONTRIBUTOR']
can_delete_roles = ['ADMIN', 'EDITOR']
can_create_roles = ['ADMIN', 'EDITOR', 'CONTRIBUTOR']

roles_map = {
    "Administrateur": "ADMIN",
    "Éditeur": "EDITOR",
    "Lecteur": "READER"
}


# VIEW BASED ON DB MODELS #


class GlobalModelView(ModelView):
    """Global & Shared parameters for the model views."""
    column_display_pk = True
    can_view_details = True
    can_set_page_size = False
    action_disallowed_list = ['delete']
    list_template = 'admin/list.html'

    def is_accessible(self):
        if current_user.is_authenticated:
            print(current_user.role)
            role = roles_map[current_user.role.value]
            self.can_edit = role in can_edit_roles
            self.can_delete = role in can_delete_roles
            self.can_create = role in can_create_roles
        else:
            self.can_edit = False
            self.can_delete = False
            self.can_create = False
        self.can_export = True
        return True


class UserView(ModelView):
    edit_template = 'admin/edit.user.html'
    create_template = 'admin/edit.user.html'
    list_template = 'admin/list.user.html'
    column_list = ["id",
                   "username",
                   "email",
                   "role"]
    column_labels = {
        "id": "ID",
        "username": "Nom d'utilisateur",
        "role": "Rôle",
        "email": "Adresse email",
    }
    column_searchable_list = ["username", "email"]
    # hide the password hash in edit/create form
    form_excluded_columns = ["password_hash",
                             "created_at",
                             "updated_at"]

    form_columns = ["username",
                    "email",
                    "role",
                    "new_password"]

    form_extra_fields = {
        "new_password": PasswordField("Nouveau mot de passe",
                                      id="new_password_field"),

    }

    @expose("/generate_password/", methods=["GET", "POST"])
    def new_password(self):
        if request.method in ["GET", "POST"]:
            password = User.generate_password()

            return jsonify({"password": password}), 200
        return jsonify({"error": "No password provided"}), 400

    def on_model_change(self, form, model, is_created):
        if form.new_password.data:
            if model.id == 1:
                if current_user.id != 1:
                    flash("Vous ne pouvez pas modifier le mot de passe de ce compte administrateur.", "danger")
                else:

                    model.set_password(form.new_password.data)
                    session.commit()
                    return model
            else:
                model.set_password(form.new_password.data)
                session.commit()
                return model

        if is_created:
            model.set_password(form.new_password.data)
            session.commit()
            return model

    def delete_model(self, model):
        if model.id == current_user.id:
            flash("Vous ne pouvez pas supprimer votre propre compte.", "danger")
            return False
        if model.id == 1:
            flash("Vous ne pouvez pas supprimer ce compte administrateur.", "danger")
            return False
        if model.role == "Administrateur":
            role = roles_map[model.role.value]
            if role != "ADMIN":
                flash("Vous ne pouvez pas supprimer un compte administrateur.", "danger")
                return False

        return super().delete_model(model)

    def is_accessible(self):
        access_view = ['ADMIN']
        if current_user.is_authenticated:
            role = roles_map[current_user.role.value]
            return role in access_view
        else:
            return False


class FamilyRelationshipView(GlobalModelView):
    """View for the family relationship model."""
    column_list = ['id', '_id_endp', 'person', 'relation_type', 'relative']
    column_labels = {'id': 'ID',
                     '_id_endp': 'ID e-NDP',
                     'person': 'Personne',
                     'relative': 'Personne liée',
                     'relation_type': 'Relation',
                     'person.pref_label': 'Personne',
                     'relative.pref_label': 'Personne liée'}
    column_searchable_list = ['person.pref_label', 'relative.pref_label', '_id_endp']


class KbLinksView(GlobalModelView):
    """View for the person kb links model."""
    column_list = ['id', '_id_endp', 'person', 'type_kb', 'url']
    column_labels = {'id': 'ID',
                     '_id_endp': 'ID e-NDP',
                     'person': 'Personne',
                     'type_kb': 'Type',
                     'url': 'Lien',
                     'person.pref_label': 'Personne'}
    column_sortable_list = ['id', 'type_kb']
    column_searchable_list = ['person.pref_label', '_id_endp']
    column_formatters = {'url': _hyperlink_item_list}


class EventView(GlobalModelView):
    """View for the person events model."""
    column_list = ['id',
                   '_id_endp',
                   'person',
                   'type',
                   'place_term',
                   'thesaurus_term_person',
                   'predecessor_id',
                   'date',
                   'image_url',
                   'comment']
    column_labels = {
        'id': 'ID',
        '_id_endp': 'ID e-NDP',
        'person': 'Personne',
        'type': 'Type',
        'place_term': 'Lieu',
        'thesaurus_term_person': 'Terme',
        'predecessor_id': 'Prédécesseur',
        'date': 'Date',
        'image_url': 'Image',
        'comment': 'Note',
        'person.pref_label': 'Personne',
        'place_term.term': 'Lieu',
        'thesaurus_term_person.term': 'Terme',
    }
    column_formatters = {
        'comment': _markup_interpret,
        'image_url': _thumbnail_interpret,
    }
    column_sortable_list = ['id', 'type', 'date', 'image_url']
    column_searchable_list = ['person.pref_label', 'place_term.term', 'thesaurus_term_person.term', 'date', 'image_url',
                              '_id_endp']
    column_filters = ['type', 'date', 'person.pref_label', 'place_term.term', 'thesaurus_term_person.term', 'image_url']


class ReferentialView(GlobalModelView):
    """View for the thesauri model."""
    edit_template = 'admin/edit_thesaurus.html'
    create_template = 'admin/edit_thesaurus.html'
    column_labels = {"term": "Terme",
                     "term_fr": "Terme (fr)",
                     "term_definition": "Définition",
                     "topic": "Topic",
                     "id": "ID",
                     "_id_endp": "ID e-NDP"}
    column_searchable_list = ["term", "term_fr"]
    column_list = ["id", '_id_endp', "topic", "term", "term_fr", "term_definition"]
    form_excluded_columns = ['events',
                             'term_position',
                             'map_place_label_id',
                             'map_place_label_new',
                             'map_place_label_old',
                             'map_place_before_restore_url',
                             'map_place_after_restore_url',
                             'map_place_ark'
                             ]
    form_args = {
        "topic": {
            "label": _format_label_form_with_tooltip("Topic", "Topic dans le thesaurus")
        }
    }

    def on_model_change(self, form, model, is_created):
        new_id = None

        def find_term(model_db, term):
            return get_thesaurus_term(session, model=model_db, args=dict(term=term))

        def create_new_id(model_db, condition):
            return get_thesaurus_terms(session, model=model_db, condition=condition)[-1].id + 1

        if is_created:
            if model.__tablename__ == "persons_thesaurus_terms":
                is_term_already_exists(find_term(ThesaurusTerm, model.term), model.term)
                new_id = create_new_id(ThesaurusTerm, condition=ThesaurusTerm.id)
            elif model.__tablename__ == "places_thesaurus_terms":
                is_term_already_exists(find_term(PlacesTerm, model.term), model.term)
                new_id = create_new_id(PlacesTerm, condition=PlacesTerm.id)
            model.id = new_id


class PersonView(GlobalModelView):
    """View for the person model."""
    edit_template = 'admin/edit.html'
    create_template = 'admin/edit.html'
    list_template = 'admin/person_list.html'
    details_template = 'admin/person_details.html'
    # Define column that will be displayed in list view
    column_list = ["id",
                   '_id_endp',
                   "pref_label",
                   "forename_alt_labels",
                   "surname_alt_labels",
                   "death_date",
                   "first_mention_date",
                   "last_mention_date",
                   "is_canon",
                   "comment",
                   "bibliography",
                   "_created_at",
                   "_updated_at",
                   "_last_editor"]
    # Overrides column labels
    column_labels = {"id": "ID",
                     "_id_endp": "ID e-NDP",
                     "pref_label": "Personne e-NDP",
                     "forename_alt_labels": "Prénom (nomen)",
                     "surname_alt_labels": "Nom (cognomen)",
                     "death_date": "Décès",
                     "first_mention_date": "Première mention",
                     "last_mention_date": "Dernière mention",
                     "is_canon": "Chanoine ?",
                     "comment": "Commentaire",
                     "bibliography": "Bibliographie",
                     "kb_links": "Lien vers un référentiel externe",
                     "events": "Événement",
                     "family_links": "Relation familiale",
                     "_created_at": "Création",
                     "_updated_at": "Révision",
                     "_last_editor": "Dernier éditeur",
                     }
    # Define column that will be displayed in edit/create view
    form_columns = ('pref_label', 'forename_alt_labels', 'surname_alt_labels', 'death_date',
                    'first_mention_date', 'last_mention_date', 'is_canon',
                    'family_links', 'kb_links', 'comment',
                    'bibliography')
    # Activate search on specific column in list view
    column_searchable_list = ['pref_label', 'death_date', 'first_mention_date', 'last_mention_date',
                              'forename_alt_labels', 'surname_alt_labels', '_id_endp']
    column_filters = ['pref_label', 'is_canon', 'death_date', 'first_mention_date',
                      'last_mention_date', 'forename_alt_labels', 'surname_alt_labels']
    # Activate sorting & add custom label/description on specific column in edit/create view
    form_args = {
        'pref_label': {
            'label': _format_label_form_with_tooltip("Personne e-NDP",
                                                     "Libellé préférentiel "
                                                     "normalisé de la personne."),
        },
        'forename_alt_labels': {
            'label': _format_label_form_with_tooltip("Prénom (Nomen)",
                                                     "Formes alternatives du prénom. "
                                                     "Appuyer sur '<b>;</b>' ou '<b>tab</b>' pour ajouter une forme."),
            'description': "Appuyer sur '<b>;</b>' ou '<b>tab</b>' pour ajouter une forme."
        },
        'surname_alt_labels': {
            'label': _format_label_form_with_tooltip("Nom (Cognomen)",
                                                     "Formes alternatives du nom. "
                                                     "Appuyer sur '<b>;</b>' ou '<b>tab</b>' pour ajouter une forme."),
            'description': "Appuyer sur '<b>;</b>' ou '<b>tab</b>' pour ajouter une forme."
        },
        'death_date': {
            'validators': [is_valid_date],
            'label': _format_label_form_with_tooltip("Décès",
                                                     "Date de décès de la personne. "
                                                     "Au format <b>AAAA-MM-JJ</b>, "
                                                     "<b>AAAA-MM</b> ou <b>AAAA</b>. "
                                                     "Ajouter le signe <b>~</b> devant pour "
                                                     "indiquer une date approximative."),
            'description': 'Format requis : <b>AAAA-MM-JJ</b>, <b>AAAA-MM</b> ou <b>AAAA</b>. '
                           'Ajouter le signe <b>~</b> devant pour indiquer une date approximative.'
        },
        'first_mention_date': {
            'validators': [is_valid_date],
            'label': _format_label_form_with_tooltip("Première mention",
                                                     "Date de la première mention dans le registre. "
                                                     "Au format <b>AAAA-MM-JJ</b>, "
                                                     "<b>AAAA-MM</b> ou <b>AAAA</b>. "
                                                     "Ajouter le signe <b>~</b> devant pour "
                                                     "indiquer une date approximative."),
            'description': 'Format requis : <b>AAAA-MM-JJ</b>, <b>AAAA-MM</b> ou <b>AAAA</b>. '
                           'Ajouter le signe <b>~</b> devant pour indiquer une date approximative.'
        },
        'last_mention_date': {
            'validators': [is_valid_date],
            'label': _format_label_form_with_tooltip("Dernière mention",
                                                     "Date de la dernière mention dans le registre. "
                                                     "Au format <b>AAAA-MM-JJ</b>, "
                                                     "<b>AAAA-MM</b> ou <b>AAAA</b>. "
                                                     "Ajouter le signe <b>~</b> devant pour "
                                                     "indiquer une date approximative."),
            'description': 'Format requis : <b>AAAA-MM-JJ</b>, <b>AAAA-MM</b> ou <b>AAAA</b>. '
                           'Ajouter le signe <b>~</b> devant pour indiquer une date approximative.'
        },
        'is_canon': {
            'label': _format_label_form_with_tooltip("Chanoine ?",
                                                     "Cocher si la personne est un chanoine."),
        },
    }
    # Exclude column from list view
    column_exclude_list = ['forename', 'surname']
    # Exclude column from edit/create view
    form_excluded_columns = ('id', '_id_endp', 'forename', 'surname', '_created_at', '_updated_at', '_last_editor')
    # Define inline model to edit/create view
    inline_models = [
        (PersonHasKbLinks, {
            'form_columns': ['id', 'type_kb', 'url'],
            'column_labels': {'type_kb': 'Base de connaissance', 'url': 'URL'},
            'form_overrides': dict(type_kb=Select2DynamicWidget),
            'form_args': dict(url=dict(default='www.wikidata.org/entity/<ID>',
                                       description="URL de la ressource. "
                                                   "Remplacer &lt;ID&gt; "
                                                   "par l'identifiant de la ressource.")),

        }),
        (
            PersonHasFamilyRelationshipType,
            dict(
                form_columns=["id", "relation_type", "relative"],
                column_labels={"relation_type": "Type", "relative": "Personne liée"}

            )
        ),
        (
            Event, dict(
                form_columns=["id", "type", "place_term", "thesaurus_term_person", "predecessor", "date", "image_url",
                              "comment"],
                column_labels={"type": "Type",
                               "place_term": "Lieu",
                               "thesaurus_term_person": "Désignation",
                               "predecessor": "Prédécesseur",
                               "date": "Date",
                               "image_url": "Image",
                               "comment": "Commentaire"},
                form_overrides=dict(image_url=Select2NakalaChoicesWidget),  # not implemented yet
                form_args=dict(
                    date=dict(validators=[is_valid_date], description="Date de l'événement. "
                                                                      "Au format <b>AAAA-MM-JJ</b>, "
                                                                      "<b>AAAA-MM</b> ou <b>AAAA</b>. "
                                                                      "Ajouter le signe <b>~</b> devant "
                                                                      "pour indiquer une date approximative."),
                    comment=dict(label="Note"),
                    image_url=dict(description="Rechercher et/ou sélectionner une image sur Nakala."
                                               " Pour accéder aux images des registres rendez-vous sur "
                                               "<a href='https://nakala.fr/collection/10.34847/nkl.03cbi521' "
                                               "target='_blank'><img src='https://nakala.fr/build/images/nakala.png' "
                                               "style='width: 24px; vertical-align: -8px; margin-right: -2px;'> "
                                               "Nakala</a>",
                                   )
                ),
            )

        ),
    ]
    # Define column formatter (custom display)
    column_formatters = {
        'pref_label': _bold_item_list,
        'is_canon': _color_on_bool,
        'comment': _markup_interpret,
        'bibliography': _markup_interpret,
        '_created_at': _dateformat,
        '_updated_at': _dateformat,
    }
    # Define form widget arguments
    form_widget_args = {
        'forename_alt_labels': {
            'class': 'input-select-tag-form-1 form-control'
        },
        'surname_alt_labels': {
            'class': 'input-select-tag-form-2 form-control'
        },
    }

    def get_list_columns(self):
        """Return list of columns to display in list view."""
        return super(PersonView, self).get_list_columns()

    def get_list_form(self):
        """Return list of columns to display in list form."""
        return super(PersonView, self).get_list_form()

    def render(self, template, **kwargs):
        """Render a template with the given context."""
        if template == "admin/person_details.html":
            events = get_events(session, {
                'id': kwargs['model'].id
            })['events']
            id_events = [evt.id for evt in get_person(session, {'id': kwargs['model'].id}).events]
            if len(events) == len(id_events):
                return super(PersonView, self).render(template, **kwargs, events=list(zip(id_events, events)))
            else:
                return super(PersonView, self).render(template, **kwargs)
        return super(PersonView, self).render(template, **kwargs)

    """
    def get_query(self):
        # Overload FTS in Model View.
        query = super(PersonView, self).get_query()
        search = request.args.get('search').lower().strip()
        if search:
            q = query.filter(
                or_(
                    self.model.pref_label.like(f"{search}%"),
                    self.model.forename_alt_labels.like(f"%{search}%"),
                    self.model.surname_alt_labels.like(f"%{search}%"),
                )
            )
            return q
        return query

    def get_count_query(self):
        # Overload FTS counter in Model View.
        query = super(PersonView, self).get_count_query()
        search = request.args.get('search').lower().strip()
        if search:
            return query.filter(
                or_(
                    self.model.pref_label.like(f"{search}%"),
                    self.model.forename_alt_labels.like(f"%{search}%"),
                    self.model.surname_alt_labels.like(f"%{search}%"),
                )
            )
        return query.count()
    """

    @expose('/get_persons_alt_labels/', methods=('GET', 'POST'))
    def get_alt_labels(self):
        """Return list of alternative labels for a given person. (Use by Select2DynamicField)"""
        if request.method == 'POST' or request.method == 'GET':
            type_label = request.form.get('type_label')
            person_pref_label = request.form.get('person_pref_label')
            labels = []
            person = get_person(session, dict(pref_label=person_pref_label))
            if type_label == "forename":
                labels = person.forename_alt_labels
            if type_label == "surname":
                labels = person.surname_alt_labels

            return jsonify(labels.split(','))

    @expose('/get_nakala_data_identifiers/', methods=('GET', 'POST'))
    def get_nakala_data_identifiers(self):
        """Return list of data identifiers from Nakala. (Use by Select2NakalaChoicesWidget)"""
        if request.method == 'POST' or request.method == 'GET':
            data = request.data.decode('utf-8')
            register_identifier = json.loads(data)['register_identifier']
            return jsonify({
                'register_number': register_identifier,
                'nakala_identifier': NAKALA_DATA_IDENTIFIERS[register_identifier]
            })

    @expose('/get_nakala_images/', methods=['GET'])
    def get_nakala_images(self):
        """Return filtered list of images from Nakala (grouped) for Select2."""
        if request.method == 'GET':
            query = request.args.get('q', '').lower()
            print(query)

            if not query:
                return jsonify([])

            filtered = []
            for group in NAKALA_IMAGES["results"]:
                matching_children = [
                    child for child in group["children"]
                    if query in child["text"].lower()
                ]
                if matching_children:
                    filtered.append({
                        "text": group["text"],
                        "children": matching_children[:50]  # limite à 50 enfants par groupe
                    })

            return jsonify(filtered)

    def on_model_change(self, form, model, is_created):
        """Update model before saving it. Custom actions on model change."""
        # Check if kb_links are valid
        is_valid_kb_links(model.kb_links)
        is_family_link_valid(model.family_links)
        is_family_link_circular(model.family_links)
        if model.__tablename__ == "persons":
            model._last_editor = current_user.username


# SPECIFIC VIEW FOR ADMINISTRATION #


class AdminView(AdminIndexView):
    """Custom view for administration."""

    @expose('/login', methods=('GET', 'POST'))
    def login(self):
        """Login view."""
        if current_user.is_authenticated:
            return redirect(url_for('admin.index'))
        form = LoginForm()
        if form.validate_on_submit():
            user = get_user(session, dict(username=form.username.data))
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                flash(f'Vous êtes connecté en tant que {current_user.username} !', 'success')
                return redirect(url_for('admin.index'))
            else:
                flash('Identifiant ou mot de passe incorrect !', 'danger')
                return self.render('admin/login.html', form=form)
        return self.render('admin/login.html', form=form)

    @expose('/logout', methods=('GET', 'POST'))
    def logout(self):
        """Logout view."""
        logout_user()
        flash('Vous êtes déconnecté !', 'warning')
        return redirect(url_for('admin.index'))


class AboutView(BaseView):
    """Custom view for database documentation."""

    @expose('/')
    def index(self):
        """Renders automatic documentation of database in html view."""
        return self.render('admin/about/documentation_db.html')

    @expose('/')
    def database_documentation(self):
        """Renders automatic documentation of database in html view."""
        return self.render('admin/about/documentation_db.html')

    @expose('/contacts')
    def contacts(self):
        """Renders contacts in html view."""
        return self.render('admin/about/contacts.html')

    @expose('/credits')
    def credits(self):
        """Renders credits in html view."""
        return self.render('admin/about/credits.html')
