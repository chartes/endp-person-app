"""
views.py

Model views for the admin interface.
"""

import re

from flask import redirect, url_for, flash, jsonify, Markup
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.filters import BaseSQLAFilter
from flask_admin import BaseView, expose, AdminIndexView


from wtforms import ValidationError, TextAreaField
from wtforms.widgets import TextArea


from flask_login import current_user, logout_user, login_user


from ..models import (User,
                     Person,
                     Event,
                     PersonHasKbLinks,
                     PersonHasFamilyRelationshipType,
                     PlacesTerm,
                     ThesaurusTerm,
                     FamilyRelationshipLabels,
                     KnowledgeBaseLabels)

from ..database import session
from .forms import LoginForm


class SearchFilter(BaseSQLAFilter):
    def __init__(self, column, name, options=None, data_type=None):
        super(SearchFilter, self).__init__(column, name, options, data_type)
        self.column = column

    def apply(self, query, value, alias=None):
        if value is not None:
            search_term = f"%{value}%"
            column_filter = self.column.ilike(search_term)
            return query.filter(column_filter)
        return query

    def operation(self):
        return u'like'

class FilterColumn(BaseSQLAFilter):
    def __init__(self, column, label=None, options=None, name=None, col=None):
        super(FilterColumn, self).__init__(column, label, options, name)
        self.column = column
        self.col = col

    def apply(self, query, value, alias=None):
        return query.filter(self.column == value)

    def operation(self):
        return u'equals'

    def get_options(self, view):
        model_class = self.column.class_
        column = getattr(model_class, self.col, None)

        if column:
            items = view.session.query(column).distinct().order_by(column)
            return [(item[0], item[0]) for item in items]

        return [item for item in session.query(Person).all()]

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


def format_enum(enum_class):
    return [choice for choice in enum_class]


def format_enum_value(value):
    return value.value


class OrderInlineModel(ModelView):
    column_formatters = {
        'type_kb': format_enum_value
    }


class CKTextAreaWidget(TextArea):
    def __call__(self, field, **kwargs):
        if kwargs.get('class'):
            kwargs['class'] += ' ckeditor'
        else:
            kwargs.setdefault('class', 'ckeditor')
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)


class CKTextAreaField(TextAreaField):
    widget = CKTextAreaWidget()

    # create admin view for Person

class DataShowView(ModelView):
    can_edit = False
    can_delete = False
    can_create = False
    can_export = True

    column_display_pk = True

    def is_accessible(self):
        return current_user.is_authenticated

class DataEventView(DataShowView):
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
        print(model.__tablename__)
        if is_created:
            if model.__tablename__ == "persons_thesaurus_terms":
                id = session.query(ThesaurusTerm).order_by(ThesaurusTerm.id).all()[-1].id + 1
            elif model.__tablename__ == "places_thesaurus_terms":
                id = session.query(PlacesTerm).order_by(PlacesTerm.id).all()[-1].id + 1
            model.id = id


class PersonView(ModelView):
    can_export = True
    can_view_details = False
    column_display_pk = True
    #create_template = 'admin/edit.html'
    #edit_template = 'admin/edit.html'
    # column_display_pk = False
    # column_hide_backrefs = False

    def _markup_interpret(self, context, model, name):
        item = getattr(model, name)
        if item is None:
            item = ""
        return Markup(item)

    def _bold_item_list(self, context, model, name):
        item = getattr(model, name)
        return Markup(f"<b>{item}</b>")

    def _color_on_bool(self, context, model, name):
        item = getattr(model, name)
        if item:
            return Markup(f"<span class='glyphicon glyphicon glyphicon-ok' style='color: #2ecc71;'></span>")
        else:
            return Markup(f"<span class='glyphicon glyphicon glyphicon-remove' style='color: #BE0A25;'></span>")

    def _dateformat(self, context, model, name):
        item = getattr(model, name)
        return item.strftime("%Y-%m-%d %H:%M:%S")

    extra_js = ['//cdn.ckeditor.com/4.6.0/basic/ckeditor.js']

    column_searchable_list = ['pref_label', 'death_date', 'first_mention_date', 'last_mention_date', 'forename_alt_labels', 'surname_alt_labels']
    # column_sortable_list = ['pref_label', 'death_date']
    #
    # order of columns in the list view
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
                    'first_mention_date', 'last_mention_date', 'is_canon', 'family_links', 'kb_links', 'comment',
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
    column_descriptions = {
        "pref_label": "Il s'agit ici de la forme préférée du nom de la personne, c'est-à-dire la forme normalisée utilisée dans l'ensemble de l'application e-NDP.",
        "forename_alt_labels": "Il s'agit ici des formes alternatives du prénom de la personne, c'est-à-dire les formes non normalisées utilisées dans les sources.",
        "surname_alt_labels": "Il s'agit ici des formes alternatives du nom de la personne, c'est-à-dire les formes non normalisées utilisées dans les sources.",
        "death_date": "Il s'agit ici de la date de décès de la personne, si elle est connue. Sous la forme AAAA-MM-JJ, ou AAAA-MM, ou AAAA, ou ~AAAA, ou ~AAAA-MM, ou ~AAAA-MM-JJ (date approximative). Exemple : 1234-56-78, ~1234-56, ~1234, 1234, ~1234-56-78, ~1234-56, ~1234.",
        "first_mention_date": "Il s'agit ici de la date de la première mention de la personne dans un registre, si elle est connue. Sous la forme AAAA-MM-JJ, ou AAAA-MM, ou AAAA, ou ~AAAA, ou ~AAAA-MM, ou ~AAAA-MM-JJ (date approximative). Exemple : 1234-56-78, ~1234-56, ~1234, 1234, ~1234-56-78, ~1234-56, ~1234.",
        "last_mention_date": "Il s'agit ici de la date de la dernière mention de la personne  dans un registre, si elle est connue. Sous la forme AAAA-MM-JJ, ou AAAA-MM, ou AAAA, ou ~AAAA, ou ~AAAA-MM, ou ~AAAA-MM-JJ (date approximative). Exemple : 1234-56-78, ~1234-56, ~1234, 1234, ~1234-56-78, ~1234-56, ~1234.",
    }
    form_excluded_columns = ('id', '_id_endp', 'forename', 'surname', '_created_at', '_updated_at', '_last_editor')
    # inline_models = [
    #    (PersonHasKbLinks, dict(form_columns=["person_id", "type_kb", "url"]),),
    # ]

    inline_models = [(
        PersonHasKbLinks,
        dict(
            # form_choices=dict(
            # type_kb=[(choice.name,choice.value) for choice in KnowledgeBaseLabels]),
            form_columns=["id", "type_kb", "url"],
            column_labels={"type_kb": "Type", "url": "URL"},
            # form_widget_args=dict(type_kb=dict(widget=Select2Widget()))
            # form_excluded_columns=("person_id", "id")
        )
    ),
        (
            PersonHasFamilyRelationshipType,
            dict(
                # form_choices=dict(
                # relation_type=format_enum(FamilyRelationshipLabels)),
                form_columns=["id", "relation_type", "relative"],
                column_labels={"relation_type": "Type", "relative": "Personne liée"}

            )
        ),
        (
            Event, dict(
                # form_choices=dict(
                #    type=format_enum(EventTypeLabels)),
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
        'comment': CKTextAreaField,
        'bibliography': CKTextAreaField,
    }

    form_choices = {
        'type_kb': format_enum(KnowledgeBaseLabels),
        'relation_type': format_enum(FamilyRelationshipLabels)
    }



    column_filters = [FilterColumn(column=Person.pref_label, label='Personne e-NDP', col='pref_label')]
    #column_filters = [FilterColumn(Person.pref_label, label='', col='pref_label')]


    # form_args = dict(
    #    forename_alt_labels=dict(validators=[is_separated_by_semicolons]),
    #    surname_alt_labels=dict(validators=[is_separated_by_semicolons]),
    #    death_date=dict(validators=[is_valid_date]),
    #    first_mention_date=dict(validators=[is_valid_date]),
    #    last_mention_date=dict(validators=[is_valid_date])
    # )

    def is_accessible(self):
        return current_user.is_authenticated

    """
    def on_model_change(self, form, model, is_created):

        {"pref_label": "Forme normalisée e-NDP",
                     "forename": "Prénom (nomen, premier prénom seulement)",
                     "forename_alt_labels": "formes du prénom (nomen)",
                     "surname": "Nom (cognomen, premier nom seulement)",
                     "surname_alt_labels": "formes du nom (cognomen)",
                     "death_date": "Date de décès",
                     "first_mention_date": "Date de la première mention",
                     "last_mention_date": "Date de la dernière mention",
                     "is_canon": "Chanoine ?",
                     "comment": "Commentaire",
                     "bibliography": "Bibliographie",
                     "kb_links": "Lien vers un référentiel externe",
                     "events": "Événement",
                     "family_links": "Relation familiale",}
    """


    def on_model_change(self, form, model, is_created):
        if model.__tablename__ == "persons":
            model._last_editor = current_user.username
            #if is_created:
            #model.id = session.query(Person).order_by(Person.id).all()[-1].id + 1

    #@expose('/')
    #def index_view(self):
    #    self._refresh_filters_cache()
    #    return super(PersonView, self).index_view()


    # def inaccessible_callback(self, name, **kwargs):
    #    return redirect(url_for('login'))


# class LoginMenuLink(MenuLink):
#    def is_accessible(self):
#        return not current_user.is_authenticated

# class LogoutMenuLink(MenuLink):
#        def is_accessible(self):
#            return current_user.is_authenticated


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


class DashboardView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/dashboard.html')

    @expose('/chart', methods=['GET', 'POST'])
    def data_for_chart(self):
        print('ici')
        return jsonify({
            'persons': int(session.query(Person).count()),
            'persons_terms': int(session.query(ThesaurusTerm).count()),
            'places_terms': int(session.query(PlacesTerm).count())
        })

    def is_accessible(self):
        return current_user.is_authenticated