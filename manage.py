"""
manage.py

This file is the entry point for manage specific DB migrations.
To run API use ./run.sh instead.
"""

from api.cli import make_cli

cli = make_cli()

if __name__ == "__main__":
    cli()
