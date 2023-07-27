"""
views.py

Model views for the admin interface.
"""
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


from ..models import (User,
                      Person,
                      Event,
                      PersonHasKbLinks,
                      PersonHasFamilyRelationshipType,
                      PlacesTerm,
                      ThesaurusTerm)

from ..database import session
from .forms import LoginForm
from .formaters import (_markup_interpret,
                        _bold_item_list,
                        _color_on_bool,
                        _dateformat,
                        _hyperlink_item_list)
from .validators import (is_valid_date,
                         is_valid_kb_links,
                         is_term_already_exists)
from .widgets import Select2DynamicWidget


EDIT_ENDPOINTS = ["person", "placesterm", "thesaurusterm"]


# VIEW BASED ON DB MODELS #


class GlobalModelView(ModelView):
    """Global & Shared parameters for the model views."""
    column_display_pk = True
    can_view_details = True

    def is_accessible(self):
        if self.endpoint in EDIT_ENDPOINTS:
            self.can_edit = current_user.is_authenticated
            self.can_delete = current_user.is_authenticated
            self.can_create = current_user.is_authenticated
            self.can_export = True
        else:
            self.can_edit = False
            self.can_delete = False
            self.can_create = False
            self.can_export = True
        return True


class FamilyRelationshipView(GlobalModelView):
    """View for the family relationship model."""
    column_list = ['id', 'person', 'relative', 'relation_type']
    column_labels = {'person': 'Personne',
                     'relative': 'Personne liée',
                     'relation_type': 'Relation',
                     'person.pref_label': 'Personne',
                     'relative.pref_label': 'Personne liée'}
    column_searchable_list = ['person.pref_label', 'relative.pref_label']


class KbLinksView(GlobalModelView):
    """View for the person kb links model."""
    column_list = ['id', 'person', 'type_kb', 'url']
    column_labels = {'person': 'Personne',
                     'type_kb': 'Type',
                      'url': 'Lien',
                      'person.pref_label': 'Personne'}
    column_sortable_list = ['id', 'type_kb']
    column_searchable_list = ['person.pref_label']
    column_formatters = {'url': _hyperlink_item_list}


class EventView(GlobalModelView):
    """View for the person events model."""
    column_list = ['id', 'person', 'type', 'place_term', 'thesaurus_term_person', 'predecessor_id', 'date', 'image_url', 'comment']
    column_labels = {
        'person': 'Personne',
        'type': 'Type',
        'place_term': 'Lieu',
        'thesaurus_term_person': 'Terme',
        'predecessor_id': 'Prédécesseur',
        'date': 'Date',
        'image_url': 'Image',
        'comment': 'Commentaire',
        'person.pref_label': 'Personne',
        'place_term.term': 'Lieu',
        'thesaurus_term_person.term': 'Terme',
    }
    column_sortable_list = ['id', 'type', 'date', 'image_url']
    column_searchable_list = ['person.pref_label', 'place_term.term', 'thesaurus_term_person.term', 'date', 'image_url']
    column_filters = ['type', 'date', 'person.pref_label', 'place_term.term', 'thesaurus_term_person.term', 'image_url']


class ReferentialView(GlobalModelView):
    """View for the thesauri model."""
    column_labels = {"term": "Terme",
                     "term_fr": "Terme (fr)",
                     "term_definition": "Définition",
                     "Topic": "Thème"}
    column_searchable_list = ["term", "term_fr"]
    column_list = ["id", "_id_endp", "topic", "term", "term_fr", "term_definition"]
    form_excluded_columns = ['term_position', 'events']

    def on_model_change(self, form, model, is_created):
        new_id = None

        def find_term(model_db, term):
            return session.query(model_db).filter_by(term=term).first()

        if is_created:
            if model.__tablename__ == "persons_thesaurus_terms":
                is_term_already_exists(find_term(ThesaurusTerm, model.term), model.term)
                new_id = session.query(ThesaurusTerm).order_by(ThesaurusTerm.id).all()[-1].id + 1
            elif model.__tablename__ == "places_thesaurus_terms":
                is_term_already_exists(find_term(PlacesTerm, model.term), model.term)
                new_id = session.query(PlacesTerm).order_by(PlacesTerm.id).all()[-1].id + 1
            model.id = new_id


class PersonView(GlobalModelView):
    """View for the person model."""
    edit_template = 'admin/edit.html'
    create_template = 'admin/edit.html'
    # Define column that will be displayed in list view
    column_list = ["id",
                   "_id_endp",
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
    column_labels = {"_id_endp": "Id e-NDP",
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
                              'forename_alt_labels', 'surname_alt_labels']
    column_filters = ['pref_label', 'is_canon', 'death_date', 'first_mention_date',
                      'last_mention_date', 'forename_alt_labels', 'surname_alt_labels']
    # Activate sorting & add custom label/description on specific column in edit/create view
    form_args = {
        'forename_alt_labels': {
            'label': 'Prénom (Nomen)',
            'description': "Formes alternatives du prénom. "
                           "Appuyer sur '<b>;</b>' ou '<b>tab</b>' pour ajouter une forme.",
        },
        'surname_alt_labels': {
            'label': 'Nom (Cognomen)',
            'description': "Formes alternatives du nom. "
                           "Appuyer sur '<b>;</b>' ou '<b>tab</b>' pour ajouter une forme.",
        },
        'death_date': {
            'validators': [is_valid_date],
        },
        'first_mention_date': {
            'validators': [is_valid_date],
        },
        'last_mention_date': {
            'validators': [is_valid_date],
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
            'form_args': dict(url=dict(default='www.wikidata.org/entity/<ID>')),

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
                form_columns=["id", "type", "place_term", "thesaurus_term_person", "date", "image_url", "comment"],
                column_labels={"type": "Type",
                               "place_term": "Lieu",
                               "thesaurus_term_person": "Désignation",
                               "date": "Date",
                               "image_url": "URL de l'image",
                               "comment": "Commentaire"},
                form_args=dict(
                    date=dict(validators=[is_valid_date]),
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
        return super(PersonView, self).render(template, **kwargs)

    @expose('/get_persons_alt_labels/', methods=('GET', 'POST'))
    def get_alt_labels(self):
        """Return list of alternative labels for a given person. (Use by Select2DynamicField)"""
        if request.method == 'POST' or request.method == 'GET':
            type_label = request.form.get('type_label')
            person_pref_label = request.form.get('person_pref_label')
            labels = []
            person = session.query(Person).filter_by(pref_label=person_pref_label).first()
            if type_label == "forename":
                labels = person.forename_alt_labels
            if type_label == "surname":
                labels = person.surname_alt_labels

            return jsonify(labels.split(','))

    def on_model_change(self, form, model, is_created):
        """Update model before saving it. Custom actions on model change."""
        # Check if kb_links are valid
        is_valid_kb_links(model.kb_links)
        if model.__tablename__ == "persons":
            model._last_editor = current_user.username


# SPECIFIC VIEW FOR ADMINISTRATION #


class MyAdminView(AdminIndexView):
    """Custom view for administration."""
    @expose('/login', methods=('GET', 'POST'))
    def login(self):
        """Login view."""
        if current_user.is_authenticated:
            return redirect(url_for('admin.index'))
        form = LoginForm()
        if form.validate_on_submit():
            user = session.query(User).filter_by(username=form.username.data).first()
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


class DatabaseDocumentationView(BaseView):
    """Custom view for database documentation."""
    @expose('/')
    def index(self):
        """Renders automatic documentation of database in html view."""
        return self.render('admin/documentation_db.html')

