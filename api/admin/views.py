"""
views.py

Model views for the admin interface.
"""

import re

from flask import redirect, url_for, flash, jsonify
from flask_admin.contrib.sqla import ModelView
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

    def is_accessible(self):
        return current_user.is_authenticated


class ReferentialView(ModelView):
    can_edit = True
    can_delete = True
    can_create = True
    can_export = True

    column_labels = {"term": "Terme",
                     "term_fr": "Terme (fr)",
                     "term_definition": "Définition",
                     "term_position": "Ordre",
                     "Topic": "Thème"}

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
    can_view_details = True
    # create_template = 'admin/edit.html'
    # edit_template = 'admin/edit.html'
    # column_display_pk = False

    extra_js = ['//cdn.ckeditor.com/4.6.0/basic/ckeditor.js']
    form_overrides = {
        'comment': CKTextAreaField,
        'bibliography': CKTextAreaField,
    }

    form_choices = {
        'type_kb': format_enum(KnowledgeBaseLabels),
        'relation_type': format_enum(FamilyRelationshipLabels)
    }
    column_searchable_list = ['pref_label', 'death_date']
    # column_sortable_list = ['pref_label', 'death_date']
    form_columns = ('pref_label', 'forename_alt_labels', 'surname_alt_labels', 'death_date',
                    'first_mention_date', 'last_mention_date', 'is_canon', 'family_links', 'kb_links', 'comment',
                    'bibliography')
    column_labels = {"pref_label": "Forme normalisée e-NDP",
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
                     "family_links": "Relation familiale", }
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