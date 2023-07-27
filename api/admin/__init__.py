"""
This main module contains the admin interface generation
with flask-admin to manage the database.
"""

from flask import Flask

from flask_admin import Admin
from flask_babelex import Babel
from flask_login import LoginManager


from .views import (PersonView,
                    FamilyRelationshipView,
                    EventView,
                    KbLinksView,
                    ReferentialView,
                    Person,
                    Event,
                    PersonHasFamilyRelationshipType,
                    PersonHasKbLinks,
                    ThesaurusTerm,
                    PlacesTerm,
                    DatabaseDocumentationView,
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

    # Register views #
    for view in [
        PersonView(Person,
                   session,
                   name='Personnes',
                   menu_icon_type='glyph',
                   menu_icon_value='glyphicon-user',
                   url='person',
                   endpoint='person'),
        EventView(Event,
                  session,
                  name='Événements',
                  category="Autres"),
        KbLinksView(PersonHasKbLinks,
                    session,
                    name='Liens vers la base de connaissances',
                    category="Autres"),
        FamilyRelationshipView(PersonHasFamilyRelationshipType,
                               session,
                               name='Relations familiales',
                               category="Autres"),
        ReferentialView(ThesaurusTerm,
                        session,
                        name='Termes personnes',
                        category="Thesauri"),
        ReferentialView(PlacesTerm,
                        session,
                        name='Termes lieux',
                        category="Thesauri"),
        DatabaseDocumentationView(
            name='Documentation de la base de données',
            menu_icon_type='glyph',
            menu_icon_value='glyphicon-book')
    ]:
        admin.add_view(view)
    return flask_app
