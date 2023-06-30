"""
This main module contains the admin interface generation
with flask-admin to manage the database.
"""

from flask import Flask

from flask_admin import Admin
from flask_babelex import Babel
from flask_ckeditor import CKEditor
from flask_login import LoginManager


from .views import (PersonView,
                    DataShowView,
                    DataEventView,
                    ReferentialView,
                    Person,
                    Event,
                    PersonHasFamilyRelationshipType,
                    PersonHasKbLinks,
                    ThesaurusTerm,
                    PlacesTerm,
                    DatabaseDocumentationView,
                    DashboardView,
                    MyAdminView)
from ..models import User
from ..config import settings, BASE_DIR
from ..database import session


def create_admin_interface() -> Flask:
    """
    Create the admin interface for the database.
    :return: Flask app
    :rtype: Flask
    """
    # create flask app for the admin
    flask_app = Flask(__name__,
                      template_folder=BASE_DIR / 'api/templates',
                      static_folder=BASE_DIR / 'api/static')

    # flask extensions #
    Babel(flask_app)
    CKEditor(flask_app)
    admin = Admin(flask_app,
                  name='e-NDP DB Administration',
                  template_mode='bootstrap3',
                  url="/admin",
                  endpoint="admin",
                  index_view=MyAdminView())
    login = LoginManager(flask_app)

    @login.user_loader
    def load_user(user_id):
        return session.query(User).get(user_id)

    # flask configuration #
    flask_app.config['SECRET_KEY'] = str(settings.FLASK_SECRET_KEY)
    flask_app.config['BABEL_DEFAULT_LOCALE'] = str(settings.FLASK_BABEL_DEFAULT_LOCALE)

    # deporter les vues dans routes les importer
    # les mettre ici dans une liste et itérer pour
    # les ajouter à la méthode add_view de l'admin
    admin.add_view(
        PersonView(
            Person, session,
            name='Personnes',
            menu_icon_type='glyph',
            menu_icon_value='glyphicon-user',
            url='person',
            endpoint='person')
    )
    admin.add_view(
        DataEventView(Event,
                     session,
                     name='Événements',
                     category="Autres")
    )
    admin.add_view(
        DataShowView(PersonHasKbLinks,
                     session,
                     name='Liens vers la base de connaissances',
                     category="Autres")
    )
    admin.add_view(
        DataShowView(PersonHasFamilyRelationshipType,
                     session,
                     name='Relations familiales',
                     category="Autres")
    )
    admin.add_view(
        ReferentialView(ThesaurusTerm,
                        session,
                        name='Termes personnes',
                        category="Thesauri")
    )
    admin.add_view(
        ReferentialView(PlacesTerm,
                        session,
                        name='Termes lieux',
                        category="Thesauri")
    )
    admin.add_view(
        DashboardView(name='Tableau de bord',
                      menu_icon_type='glyph',
                      menu_icon_value='glyphicon-dashboard')
    )
    admin.add_view(
        DatabaseDocumentationView(
            name='Documentation de la base de données',
            menu_icon_type='glyph',
            menu_icon_value='glyphicon-book')
    )

    return flask_app
