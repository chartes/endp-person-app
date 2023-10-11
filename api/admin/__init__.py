"""
This main module contains the admin interface generation
with flask-admin to manage the database.
"""
from flask import Flask

from flask_admin import Admin
from flask_babelex import Babel
from flask_login import LoginManager
from flask_mail import Mail

from ..crud import get_user
from ..config import settings, BASE_DIR
from ..database import session
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
                    AdminView)


# flask app #
flask_app = Flask(__name__,
                  template_folder=BASE_DIR / 'api/templates',
                  static_folder=BASE_DIR / 'api/static')

# flask configuration #
flask_app.config['SECRET_KEY'] = str(settings.FLASK_SECRET_KEY)
flask_app.config['BABEL_DEFAULT_LOCALE'] = str(settings.FLASK_BABEL_DEFAULT_LOCALE)
flask_app.config['MAIL_SERVER'] = str(settings.FLASK_MAIL_SERVER)
flask_app.config['MAIL_PORT'] = int(settings.FLASK_MAIL_PORT)
flask_app.config['MAIL_USE_TLS'] = bool(settings.FLASK_MAIL_USE_TLS)
flask_app.config['MAIL_USE_SSL'] = bool(settings.FLASK_MAIL_USE_SSL)
flask_app.config['MAIL_USERNAME'] = str(settings.FLASK_MAIL_USERNAME)
flask_app.config['MAIL_PASSWORD'] = str(settings.FLASK_MAIL_PASSWORD)

# flask extensions #
Babel(flask_app)
admin = Admin(flask_app,
              name='e-NDP DB Administration',
              template_mode='bootstrap3',
              url="/endp-person/admin/",
              endpoint="admin",
              index_view=AdminView())
login = LoginManager(flask_app)
mail = Mail(flask_app)


@login.user_loader
def load_user(user_id):
    """load the user with the given id"""
    return get_user(session, {'id': user_id})


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


from .routes import reset_password, reset_password_request
