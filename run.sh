#!/bin/bash

###################################################################################
#                                                                                 #
# run.sh                                                                          #
# ----------                                                                      #
#                                                                                 #
# ** API main launch script **                                                    #
#                                                                                 #
# Usage:                                                                          #
#   ./run.sh <mode> [-db]                                                         #
#   <mode> : dev | prod [REQ.]                                             #
#   -db : Recreate and populate database with initial data [OPT.]                 #
#                                                                                 #
# Examples:                                                                       #
#   ./run.sh dev -db                                                              #
###################################################################################

ENV="dev"

# ajouter une commande help afficher l'aide
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  echo "run.sh - API main launch script"
  echo "Usage: ./run.sh <mode> [-db]"
  echo "  <mode> : dev | prod [REQ.]"
  echo "  -db : Recreate and populate database with initial data [OPT.]"
  exit 0
fi



# Lancer l'application en fonction du mode
echo "Loading vars env in "$1" mode..."
case "$1" in
  dev)
    ENV="dev"
    source .dev.env
    ;;
  prod)
    ENV="prod"
    source .prod.env
    ;;
  *)
    echo "Invalid mode. Please specify either 'dev' or 'prod'."
    exit 1
    ;;
esac

export ENV=$ENV

# Vérification de l'argument pour la base de données
if [[ "$2" == "-db" ]]; then
  echo "> Prepare whoosh index dir..."
  python3 manage.py index-create
  echo "> Recreate database process:"
  python3 manage.py db-recreate
  echo "> Populate database process:"
  python3 manage.py db-populate
  # whoosh index auto populate via sqlalchemy events
fi


# Lancer l'application en fonction du mode
echo "Starting the application [in "$1" mode]..."
if [[ "$1" == "dev" ]]; then
  uvicorn api.main:app --host $HOST --port $PORT --reload
elif [[ "$1" == "prod" ]]; then
  uvicorn api.main:app --host $HOST --port $PORT --workers $WORKERS
fi


