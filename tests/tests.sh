#!/bin/bash

echo "[<<** RUNNING TESTS **>>]"
echo "Loading vars env in test mode..."
export ENV="test"
source ../.test.env
echo $DB_URI
echo "Recreate database..."
python3 ../manage.py db-recreate
echo "Populate database..."
python3 ../manage.py db-populate
pytest . --disable-warnings