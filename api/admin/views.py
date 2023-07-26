"""
views.py

Model views for the admin interface.
"""
import itertools

from flask import (redirect,
                   url_for,
                   flash,
                   jsonify,
                   request, render_template_string)
from flask_admin.contrib.sqla import ModelView
from flask_admin import (BaseView,
                         expose,
                         AdminIndexView)
from flask_admin.form import rules
from flask_admin.model.form import InlineFormAdmin
from flask_admin.contrib.sqla.form import InlineModelConverter
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_login import (current_user,
                         logout_user,
                         login_user)
from flask_admin.form.widgets import Select2Widget, Select2TagsWidget
from flask_admin.form.fields import Select2TagsField
from wtforms import StringField, Form, SelectField, TextAreaField
from wtforms.widgets import TextArea


from ..models import (User,
                      Person,
                      Event,
                      PersonHasKbLinks,
                      PersonHasFamilyRelationshipType,
                      PlacesTerm,
                      ThesaurusTerm,
                      FamilyRelationshipLabels,
                      KnowledgeBaseLabels)
from api.models import _get_enum_values
from ..database import session
from .forms import LoginForm
from .formaters import (_markup_interpret,
                        _bold_item_list,
                        _color_on_bool,
                        _dateformat)
from .validators import (is_valid_date,
                         is_separated_by_semicolons)
from .widgets import CKTextAreaField, QuillTextAreaField


KB_URL_MAPPING = {
    "Wikidata": "www.wikidata.org/entity/",
    "Biblissima": "www.biblissima.com/ark:/",
    "VIAF": "www.viaf.org/viaf/",
    "DataBnF": "www.data.bnf.fr/",
    "Studium Parisiense": "www.studium.fr/",
    "Collecta": "www.collecta.fr/",
}

# Utils
def format_enum(enum_class):
    return [choice for choice in enum_class]


class GlobalModelView(ModelView):
    column_display_pk = True
    can_view_details = True
    def is_accessible(self):
        if self.endpoint == "person":
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

# TODO: create a view for family relationship
# TODO: create a view for kb links


class DataEventView(GlobalModelView):
    column_list = ['id', 'person', 'type', 'place_term', 'thesaurus_term_person', 'predecessor_id', 'date', 'image_url', 'comment']
    column_labels = {
        'person': 'Personne',
        'type': 'Type',
        'place_term': 'Lieu',
        'thesaurus_term_person': 'Terme',
        'predecessor_id': 'Prédécesseur',
        'date': 'Date',
        'image_url': 'Image',
        'comment': 'Commentaire'
    }
    column_sortable_list = ['id', 'person', 'type', 'date']
    column_searchable_list = ['person.pref_label']

class ReferentialView(ModelView):
    can_edit = True
    can_delete = True
    can_create = True
    can_export = True
    column_display_pk = True

    column_labels = {"term": "Terme",
                     "term_fr": "Terme (fr)",
                     "term_definition": "Définition",
                     "Topic": "Thème"}

    column_searchable_list = ["term", "term_fr"]
    column_list = ["id", "_id_endp", "topic", "term", "term_fr", "term_definition"]

    column_exclude_list = ['term_position']

    def is_accessible(self):
        return current_user.is_authenticated

    def on_model_change(self, form, model, is_created):
        id = None
        if is_created:
            if model.__tablename__ == "persons_thesaurus_terms":
                id = session.query(ThesaurusTerm).order_by(ThesaurusTerm.id).all()[-1].id + 1
            elif model.__tablename__ == "places_thesaurus_terms":
                id = session.query(PlacesTerm).order_by(PlacesTerm.id).all()[-1].id + 1
            model.id = id

class Select2DynamicField(SelectField):
    def __init__(self, label=None, validators=None, coerce=int, choices=None, **kwargs):
        super(Select2DynamicField, self).__init__(label, validators, coerce, choices, **kwargs)
        choices = [(label, label) for i, label in enumerate(_get_enum_values(KnowledgeBaseLabels))]
        coerce = str
        kwargs['widget'] = Select2Widget()
        kwargs['render_kw'] = {'onchange': 'fetchCorrectUrlStringFromKbSelect(this)'}

        return super(Select2DynamicField, self).__init__(label, validators, coerce, choices, **kwargs)


class PersonView(GlobalModelView):
    #can_export = True

    # can_edit = True if is not None else False
    #can_create = True if current_user.is_authenticated is not None else False
    #can_delete = True if current_user.is_authenticated is not None else False
    #column_display_pk = True
    edit_template = 'admin/edit.html'
    create_template = 'admin/edit.html'
    form_args = {
        'forename_alt_labels': {
            'label': 'Prénom (Nomen)',
            'description': "Formes alternatives du prénom. Appuyer sur '<b>;</b>' ou '<b>tab</b>' pour ajouter une forme.",
        },
        'surname_alt_labels': {
            'label': 'Nom (Cognomen)',
            'description': "Formes alternatives du nom. Appuyer sur '<b>;</b>' ou '<b>tab</b>' pour ajouter une forme.",
        },
    }



    def get_list_columns(self):
        return super(PersonView, self).get_list_columns()

    def get_list_form(self):
        return super(PersonView, self).get_list_form()


    def render(self, template, **kwargs):
        #self.extra_js = [url_for('static', filename='js/person.form.fields.js')]
        return super(PersonView, self).render(template, **kwargs)



    column_descriptions = {
        #"pref_label": "Il s'agit ici de la forme préférée du nom de la personne, c'est-à-dire la forme normalisée utilisée dans l'ensemble de l'application e-NDP.",
        #"forename_alt_labels": "Il s'agit ici des formes alternatives du prénom de la personne, c'est-à-dire les formes non normalisées utilisées dans les sources.",
        #"surname_alt_labels": "Il s'agit ici des formes alternatives du nom de la personne, c'est-à-dire les formes non normalisées utilisées dans les sources.",
        #"death_date": "Il s'agit ici de la date de décès de la personne, si elle est connue. Sous la forme AAAA-MM-JJ, ou AAAA-MM, ou AAAA, ou ~AAAA, ou ~AAAA-MM, ou ~AAAA-MM-JJ (date approximative). Exemple : 1234-56-78, ~1234-56, ~1234, 1234, ~1234-56-78, ~1234-56, ~1234.",
        #"first_mention_date": "Il s'agit ici de la date de la première mention de la personne dans un registre, si elle est connue. Sous la forme AAAA-MM-JJ, ou AAAA-MM, ou AAAA, ou ~AAAA, ou ~AAAA-MM, ou ~AAAA-MM-JJ (date approximative). Exemple : 1234-56-78, ~1234-56, ~1234, 1234, ~1234-56-78, ~1234-56, ~1234.",
        #"last_mention_date": "Il s'agit ici de la date de la dernière mention de la personne  dans un registre, si elle est connue. Sous la forme AAAA-MM-JJ, ou AAAA-MM, ou AAAA, ou ~AAAA, ou ~AAAA-MM, ou ~AAAA-MM-JJ (date approximative). Exemple : 1234-56-78, ~1234-56, ~1234, 1234, ~1234-56-78, ~1234-56, ~1234.",
    }

    # extra_js = ['//cdn.ckeditor.com/4.6.0/basic/ckeditor.js']

    column_searchable_list = ['pref_label', 'death_date', 'first_mention_date', 'last_mention_date', 'forename_alt_labels', 'surname_alt_labels']
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
    form_columns = ('pref_label', 'forename_alt_labels', 'surname_alt_labels', 'death_date',
                    'first_mention_date', 'last_mention_date', 'is_canon', 'family_links','kb_links', 'comment',
                    'bibliography')



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

    column_exclude_list = ['forename', 'surname']

    form_excluded_columns = ('id', '_id_endp', 'forename', 'surname', '_created_at', '_updated_at', '_last_editor')

    inline_models = [
        (PersonHasKbLinks, {
            'form_columns': ['type_kb', 'url'],
            'column_labels': {'type_kb': 'Base de connaissance', 'url': 'URL'},
            'form_overrides': dict(type_kb=Select2DynamicField),
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
                               "comment": "Commentaire"}
            )

        ),
    ]

    column_formatters = {
        'pref_label': _bold_item_list,
        'is_canon': _color_on_bool,
        'comment': _markup_interpret,
        'bibliography': _markup_interpret,
        '_created_at': _dateformat,
        '_updated_at': _dateformat,
    }
    form_overrides = {
        'comment': QuillTextAreaField,
        'bibliography': QuillTextAreaField,
        'pref_label': StringField,
    }

    form_widget_args = {
        'forename_alt_labels': {
            'class': 'input-select-tag-form-1 form-control'
        },
        'surname_alt_labels': {
            'class': 'input-select-tag-form-2 form-control'
        },
    }


    #form_choices = {
    #    'type_kb': format_enum(KnowledgeBaseLabels),
    #    'relation_type': format_enum(FamilyRelationshipLabels)
    #}

    @expose('/map_id/', methods=('GET', 'POST'))
    def map_id(self):
        # response from ajax request
        if request.method == 'POST':
            # get the id from the request in data
            id = request.form.get('id')
            # return the result as json
            return jsonify({'url': KB_URL_MAPPING[id]})

    @expose('/get_persons_alt_labels/', methods=('GET', 'POST'))
    def get_alt_labels(self):
        if request.method == 'POST' or request.method == 'GET':
            type_label = request.form.get('type_label')
            person_pref_label = request.form.get('person_pref_label')
            labels = []
            person = session.query(Person).filter_by(pref_label=person_pref_label).first()
            if type_label == "forename":
                labels = person.forename_alt_labels
            if type_label == "surname":
                labels = person.surname_alt_labels

            return jsonify(labels.split(';'))

    #def is_accessible(self):
    #    self.can_create = current_user.is_authenticated
    #    self.can_edit = current_user.is_authenticated
    #    self.can_delete = current_user.is_authenticated
    #    return True

    def on_model_change(self, form, model, is_created):
        if model.__tablename__ == "persons":
            model._last_editor = current_user.username





class MyAdminView(AdminIndexView):
    @expose('/login', methods=('GET', 'POST'))
    def login(self):
        if current_user.is_authenticated:
            return redirect(url_for('admin.index'))
        form = LoginForm()
        print('ici')
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
        logout_user()
        flash('Vous êtes déconnecté !', 'warning')
        return redirect(url_for('admin.index'))


class DatabaseDocumentationView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/documentation_db.html')

    def is_accessible(self):
        return current_user.is_authenticated


