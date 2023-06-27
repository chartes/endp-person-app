# E-NDP API
[![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-380/) 

[![FastAPI - API](https://img.shields.io/static/v1?label=FastAPI&message=API&color=%232E303E&style=for-the-badge&logo=fastapi&logoColor=%23009485)](https://fastapi.tiangolo.com/)
[![SQLite - DB](https://img.shields.io/static/v1?label=SQLite&message=DB&color=%2374B8E4&style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/index.html)
[![Flask - admin](https://img.shields.io/static/v1?label=Flask&message=admin&color=black&style=for-the-badge&logo=flask&logoColor=white)](https://flask-admin.readthedocs.io/en/latest/#)
[![SQLAlchemy -  orm](https://img.shields.io/badge/SQLAlchemy-_orm-red?style=for-the-badge)](https://www.sqlalchemy.org/)


## Installation

En local, cloner le dépôt GitHub :

```bash
git clone git@github.com:chartes/endp-api.git
```

Puis exécuter les commandes suivantes :

```bash
virualenv --python=python3.9 venv
source venv/bin/activate
pip install -r requirements.txt
 ```

## Lancer l'API

Les tâches courantes sont réalisées avec le script `run.sh`.

Pour une première initialisation de la base de données ou pour la recréer et lancer l'application :

```bash
   ./run.sh [dev|test] -db
```

Pour lancer l'application seule (ignorer l'argument `-db`) :

```bash
   ./run.sh [dev|test]
```

Pour contrôler le bon fonctionnement de l'application :

- la documentation de l'API se trouve à l'adresse : http://localhost:8000/api/docs
- l'interface d'administration se trouve à l'adresse : http://localhost:8000/admin/

## Ajouter un utilisateur 

```bash
   python3 manage.py create-user --username <username> --email <email> --password <password>
```

## Contrôle de la qualité du code et tests unitaires

La qualité du code et les tests unitaires sont réalisés via la CI GitHub Actions.
Cependant, pour lancer les tests en local : 

```bash
cd tests/
# lancer le contrôle de la qualité du code
chmod +x linter.sh
./linter.sh
# lancer les tests unitaires
chmod +x tests.sh
./tests.sh
```
