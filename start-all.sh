#!/bin/sh
#python manage.py dumpdata context --format=json --indent=4 > ./context/fixtures/initial_data.json
python manage.py syncdb --noinput
#python manage.py migrate
cp festos.sqlite3 half.sqlite3
#python manage.py loaddata accounts/fixtures/groups.json
#python manage.py check_permissions
#python manage.py apply_permissions
python manage.py runserver
