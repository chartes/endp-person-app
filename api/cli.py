"""
cli.py

The CLI application for common DB migrations.
"""
import sys
import os

import sqlite3
import click

from .models import User, Person
from .database import (session,
                       engine,
                       BASE)
from .database_utils import populate_db_process
from .index_fts.index_utils import (create_index,
                                    populate_index,
                                    create_store,)
from .index_fts.schemas import PersonIdxSchema
from .index_conf import (st,
                         WHOOSH_INDEX_DIR)

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
        click.confirm("This operation will populate the database, do you want to continue?", abort=True)
        try:
            populate_db_process(in_session=session)
            click.echo("✔️The database has been populated.")
        except Exception as e:
            click.echo("❌The database has not been populated.")
            click.echo(f"Error: {e}")
            sys.exit(1)

    @click.command("db_copy")
    @click.argument('source_db', type=click.Path(exists=True), required=True)
    @click.argument('target_db', type=click.Path(exists=True), required=True)
    def copy_db(source_db, target_db):
        """Copy the source database to the target database."""
        if not os.path.exists(source_db):
            click.echo(f"❌The source database {source_db} does not exist.")
            sys.exit(1)
        if not os.path.exists(target_db):
            os.remove(target_db)


        try:
            with sqlite3.connect(source_db) as source:
                with sqlite3.connect(target_db) as target:
                    source.backup(target)

            click.echo("✔️The database has been copied.")
        except Exception as e:
            click.echo("❌The database has not been copied.")
            click.echo(f"Error: {e}")
            sys.exit(1)

    @click.command("index-create")
    def index_create():
        """Create the index for full-text search. (Whoosh)"""
        click.echo("Creating the index dir to manage full-text search...")
        try:
            create_store(st, WHOOSH_INDEX_DIR)
            create_index(st, PersonIdxSchema)
            click.echo("✔️The index has been created and ready to populate.")
        except Exception as e:
            click.echo("❌The index has not been created.")
            click.echo(f"Error: {e}")
            sys.exit(1)

    @click.command("index-populate")
    def index_populate():
        """Populate index with db data.
        Normally, don't use this command, because using triggers and events
        with db-populate."""
        try:
            ix = st.open_index()
            populate_index(session, ix, Person)
            click.echo("✔️The index has been populated.")
        except Exception as e:
            click.echo("❌The index has not been populated.")
            click.echo(f"Error: {e}")
            sys.exit(1)

    @click.command("create-user")
    @click.option("--username", "-u", type=str, help="Username of the user.", required=True)
    @click.option("--email", "-e", type=str, help="Email of the user.", required=True)
    @click.option("--password", "-p", type=str, help="Password of the user.", required=True)
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

    @click.command("reset-password")
    @click.option("--username", "-u", type=str, help="Username of the user.", required=True)
    @click.option("--new-password", "-p", type=str, help="New password of the user.", required=True)
    def reset_password(username, new_password):
        try:
            user = session.query(User).filter_by(username=username).first()
            user.set_password(new_password)
            session.commit()
            click.echo(f"✔️ User {username} has been updated.")
        except Exception as e:
            session.rollback()
            click.echo(f"❌ User {username} not exist.")
            click.echo(f"Error: {e}")
            sys.exit(1)

    cli.add_command(db_create)
    cli.add_command(db_recreate)
    cli.add_command(db_populate)
    cli.add_command(copy_db)
    cli.add_command(create_user)
    cli.add_command(index_create)
    cli.add_command(index_populate)
    cli.add_command(reset_password)

    return cli
