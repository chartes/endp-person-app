"""
database_utils.py

A set of functions to populate the database with the latest version of data.
"""

import os
import sys

import pandas as pd
import yaml

from .config import BASE_DIR, settings
from .models import (Person,
                     ThesaurusTerm,
                     Event,
                     PersonHasKbLinks,
                     PlacesTerm,
                     PersonHasFamilyRelationshipType)
from .database import session

DB_MODEL_SWITCHER = {
    "persons": Person,
    "events": Event,
    "person_has_kb_links": PersonHasKbLinks,
    "person_has_family_relationships_type": PersonHasFamilyRelationshipType,
    "persons_thesaurus_terms": ThesaurusTerm,
    "places_thesaurus_terms": PlacesTerm
}


def check_path(path: str, err_msg: str):
    """Check if the path exists."""
    if not os.path.exists(path):
        print(f"Error: {err_msg}")
        sys.exit(1)


def populate_db_process():
    """Populate the database with the latest version of data."""
    # Check path and data location
    print(BASE_DIR, settings.METADATA_DATA_INTEGRITY_CHECK_PATH)
    metadata_file = os.path.join(BASE_DIR, settings.METADATA_DATA_INTEGRITY_CHECK_PATH, "metadata.yml")
    check_path(metadata_file, f"File: {metadata_file} does not exist.")
    # Read metadata file
    config = read_metadata(metadata_file)
    if config is None:
        print(f"Error: Cannot read the YAML file -> {metadata_file}.")
        sys.exit(1)
    # Extract version and data directory
    version = get_version_dir(config)
    dir_data = os.path.join(BASE_DIR, settings.METADATA_DATA_INTEGRITY_CHECK_PATH, version)
    check_path(dir_data, f"Directory: {dir_data} does not exist.")

    print(f'Recreating the database from version {version}...')
    for table in config['ressources']['tables']:
        table_metadata = get_table_metadata(table, dir_data)
        if table_metadata is None:
            sys.exit(1)
        try:
            print(f"Checking data integrity for resource: {table_metadata['name']}...")
            df = read_csv_data(table_metadata['path'], table_metadata['separator'], table_metadata['type_df'])
            print(f"Populating the table {table_metadata['name']} from {table_metadata['path']}...")
            populate_table(table_metadata['model'], df)
            print(f"✔️ Population of the table {table_metadata['name']} completed successfully.")
        except Exception as e:
            session.rollback()
            print(f"❌ Failed to populate the table {table_metadata['name']}.")
            print(f"Error: {e}")


def read_metadata(metadata_file):
    """Read the metadata file and return the parsed configuration."""
    try:
        with open(metadata_file, "r") as stream:
            config = yaml.safe_load(stream)
        return config
    except yaml.YAMLError:
        return None


def get_version_dir(config):
    """Extract and return the version directory from the configuration."""
    version = config.get('version_dir', '')
    if not version.endswith('/'):
        version = version + "/"
    return version


def get_table_metadata(table, dir_data):
    """Extract and return the metadata for a specific table."""
    try:
        table_metadata = {
            'name': table['name'],
            'path': os.path.join(dir_data, table['path']),
            'separator': table['separator'],
            'type_df': {col['name']: col['type'] for col in table['columns']},
            'model': DB_MODEL_SWITCHER[table['name']]
        }
        return table_metadata
    except Exception as e:
        return None


def read_csv_data(file_path, separator, type_df):
    """Read CSV data from a file and return a DataFrame."""
    try:
        df = pd.read_csv(file_path, sep=separator, encoding='utf-8', dtype=type_df)
        return df
    except Exception as e:
        return None


def populate_table(model, df):
    """Populate a database table with data from a DataFrame."""
    items = [model(**row.to_dict()) for _, row in df.iterrows()]
    for item in items:
        session.add(item)
        session.commit()