"""
cli.py

The CLI application for common DB migrations.
"""
import sys
import os

import click

from .models import User, Person
from .database import (session,
                       engine,
                       BASE)
from .database_utils import populate_db_process
from .index_fts.index_utils import (create_index,
                                    populate_index)
from .config import (settings, BASE_DIR)


def make_cli():
    """Create the CLI application for e-NDP development."""
    @click.group()
    def cli():
        """A CLI to manage current tasks on e-NDP database and API."""
    @click.command("db-create")
    def db_create():
        """Create the local database."""
        click.confirm("This operation will only create the database, do you want to continue?", abort=True)
        try:
            BASE.metadata.create_all(bind=engine)
            # add default users
            User.add_default_user(in_session=session)
            session.commit()
            click.echo("✔️The database has been created.")
        except Exception as e:
            click.echo("❌The database has not been created.")
            click.echo(f"Error: {e}")
            sys.exit(1)

    @click.command("db-recreate")
    def db_recreate():
        """Recreate the local database [BE CAREFUL IN PRODUCTION!]."""
        click.confirm("This operation will recreate all database, do you want to continue?", abort=True)
        try:
            BASE.metadata.drop_all(bind=engine)
            BASE.metadata.create_all(bind=engine)
            # add default users
            User.add_default_user(in_session=session)
            session.commit()
            click.echo("✔️The database has been dropped and recreated.")
        except Exception as e:
            click.echo('❌The database has not been recreated.')
            click.echo(f"Error: {e}")
            sys.exit(1)

    @click.command("db-populate")
    def db_populate():
        """populate the database with the last version of data."""
        populate_db_process(in_session=session)

    @click.command("index-create")
    def index_create():
        """Create the index for full-text search. (Whoosh)"""
        click.echo("Creating and populate the index for full-text search...")
        try:
            index_ = create_index(os.path.join(BASE_DIR, settings.WHOOSH_INDEX_DIR))
            click.echo("✔️The index has been created.")
        except Exception as e:
            click.echo("❌The index has not been created.")
            click.echo(f"Error: {e}")
            sys.exit(1)
        try:
            populate_index(session, index_, Person)
            click.echo("✔️The index has been populated.")
        except Exception as e:
            click.echo("❌The index has not been populated.")
            click.echo(f"Error: {e}")
            sys.exit(1)

    @click.command("create-user")
    @click.option("--username", "-u", type=str, help="Username of the user.")
    @click.option("--email", "-e", type=str, help="Email of the user.")
    @click.option("--password", "-p", type=str, help="Password of the user.")
    def create_user(username, email, password):
        """Create a new user."""
        try:
            user = User()
            user.username = username
            user.email = email
            user.set_password(password)
            session.add(user)
            session.commit()
            click.echo(f"✔️ User {username} has been created.")
        except Exception as e:
            session.rollback()
            click.echo(f"❌ User {username} has not been created.")
            click.echo(f"Error: {e}")
            sys.exit(1)

    cli.add_command(db_create)
    cli.add_command(db_recreate)
    cli.add_command(db_populate)
    cli.add_command(create_user)
    cli.add_command(index_create)

    return cli
