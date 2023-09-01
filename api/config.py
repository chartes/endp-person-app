"""
config.py

Settings for the application.
By default, the application will run in debug mode.
[prod | dev] only. go to tests/ for testing settings.
"""
import dotenv
import os
import pathlib

from pydantic import BaseSettings

# Set the base directory for the project
BASE_DIR = pathlib.Path(__file__).parent.parent

# Load the environment variables (by, default, the dev environment)
mode = os.environ.get("ENV", "dev")
env_file = BASE_DIR / f".{mode}.env"
dotenv.load_dotenv(env_file)


class Settings(BaseSettings):
    # Don't forget to add the new settings in the .env files

    # ~ General settings ~
    DEBUG: bool = bool(os.environ.get("DEBUG", True))
    PORT: int = int(os.environ.get("PORT", 8000))
    HOST: str = str(os.environ.get("HOST", "127.0.0.1"))
    TESTING: bool = bool(os.environ.get("TESTING", False))

    # ~ Flask settings (admin part) ~
    FLASK_SECRET_KEY: str = str(os.environ.get("FLASK_SECRET_KEY", ""))
    FLASK_BABEL_DEFAULT_LOCALE: str = str(os.environ.get("FLASK_BABEL_DEFAULT_LOCALE", "fr"))

    FLASK_MAIL_SERVER: str = str(os.environ.get("FLASK_MAIL_SERVER", ""))
    FLASK_MAIL_PORT: int = int(os.environ.get("FLASK_MAIL_PORT", 587))
    FLASK_MAIL_USE_TLS: bool = bool(os.environ.get("FLASK_MAIL_USE_TLS", True))
    FLASK_MAIL_USE_SSL: bool = bool(os.environ.get("FLASK_MAIL_USE_SSL", False))
    FLASK_MAIL_USERNAME: str = str(os.environ.get("FLASK_MAIL_USERNAME", ""))
    FLASK_MAIL_PASSWORD: str = str(os.environ.get("FLASK_MAIL_PASSWORD", ""))

    FLASK_ADMIN_NAME = str(os.environ.get("FLASK_ADMIN_NAME", "admin"))
    FLASK_ADMIN_MAIL = str(os.environ.get("FLASK_ADMIN_MAIL", ""))
    FLASK_ADMIN_ADMIN_PASSWORD = str(os.environ.get("FLASK_ADMIN_ADMIN_PASSWORD", ""))

    # ~ Database settings ~
    DB_URI: str = str(os.environ.get("DB_URI", "db/endp.dev.sqlite"))
    DB_ECHO: bool = bool(os.environ.get("DB_ECHO", False))
    METADATA_DATA_INTEGRITY_CHECK_PATH: str = str(os.environ.get("METADATA_DATA_INTEGRITY_CHECK_PATH", "ressources_db/"))

    # ~Index settings ~
    WHOOSH_INDEX_DIR: str = str(os.environ.get("WHOOSH_INDEX_DIR", "index_endp"))

    class Config:
        env_file = env_file
        env_file_encoding = "utf-8"


settings = Settings()
