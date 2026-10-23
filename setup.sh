#!/usr/bin/env bash
# One-time local setup: installs packages, creates the database, loads the CV content.
set -e
python3 -m pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py seed_cv
echo
echo "Create your administrator login:   python3 manage.py createsuperuser"
echo "Create the manager login:         python3 manage.py create_manager --username manager --password YOUR-PASSWORD"
echo "Then start the site:          python3 manage.py runserver"
echo "Site: http://127.0.0.1:8000/    Dashboard: http://127.0.0.1:8000/login/"
