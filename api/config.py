"""
config.py

Settings for the application.
By default, the application will run in debug mode.
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

    # ~ Database settings ~
    DB_URI: str = str(os.environ.get("DB_URI", "db/endp.dev.sqlite"))
    METADATA_DATA_INTEGRITY_CHECK_PATH: str = str(os.environ.get("METADATA_DATA_INTEGRITY_CHECK_PATH", "ressources_db/"))

    class Config:
        env_file = env_file
        env_file_encoding = "utf-8"


settings = Settings()
