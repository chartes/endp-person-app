# E-NDP service personne 
[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-390/) [![eNDP API CI](https://github.com/chartes/endp-api/actions/workflows/CI-tests.yml/badge.svg?branch=master)](https://github.com/chartes/endp-api/actions/workflows/CI-tests.yml)
![coverage](./tests/coverage.svg)

[![FastAPI - API](https://img.shields.io/static/v1?label=FastAPI&message=API&color=%232E303E&style=for-the-badge&logo=fastapi&logoColor=%23009485)](https://fastapi.tiangolo.com/)
[![SQLite - DB](https://img.shields.io/static/v1?label=SQLite&message=DB&color=%2374B8E4&style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/index.html)
[![Flask - admin](https://img.shields.io/static/v1?label=Flask&message=admin&color=black&style=for-the-badge&logo=flask&logoColor=white)](https://flask-admin.readthedocs.io/en/latest/#)
[![SQLAlchemy -  orm](https://img.shields.io/badge/SQLAlchemy-_orm-red?style=for-the-badge)](https://www.sqlalchemy.org/)

## Description

Ce dépôt contient le service personnes e-NDP, qui se décline de la manière suivante :
- la base de données (données intiales comprises) pour les personnes;
- l'interface d'administration pour la BD des personnes;
- l'API (+ documentation Swagger) pour interroger la BD des personnes.

## Installation

En local, cloner le dépôt GitHub :

```bash
git clone git@github.com:chartes/endp-api.git
```

Puis exécuter les commandes suivantes :

```bash
virualenv --python=python3.8 venv
source venv/bin/activate
pip install -r requirements.txt
 ```

## Lancer l'API

Les tâches courantes sont réalisées avec le script `run.sh`.

Pour une première initialisation de la base de données ou pour la recréer et lancer l'application :

```bash
   ./run.sh dev -db
```

Pour lancer l'application seule (ignorer l'argument `-db`) :

```bash
   ./run.sh dev
```

Pour contrôler le bon fonctionnement de l'application :

- la documentation de l'API se trouve à l'adresse : http://localhost:8000/api/docs
- l'interface d'administration se trouve à l'adresse : http://localhost:8000/admin/

Identifiants par défaut pour l'authentification à l'interface d'administration 
pour le développement et les tests :

- username : `admin`
- password : `admin`

## Ajouter un utilisateur 

```bash
   python3 manage.py create-user --username <username> --email <email> --password <password>
```

## Contrôle de la qualité du code et tests unitaires

La qualité du code et les tests unitaires sont réalisés via la CI GitHub Actions.
Cependant, pour lancer les tests en local : 

```bash
cd tests/
# 1. lancer le contrôle de la qualité du code
# rendre le scripts exécutable (si nécessaire)
chmod +x linter.sh
./linter.sh
# 2. lancer les tests unitaires
pytest
# 3. lancer la couverture de code
pytest --cov
```
