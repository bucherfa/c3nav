#!/bin/bash

cd /home/c3nav/c3nav
. env/bin/activate
cd src

if [ -z "$1" ]
  then
    python manage.py collectstatic --noinput
    python manage.py compress
    rm -rf /home/c3nav/static/*
    cp -r /home/c3nav/c3nav/src/c3nav/static.dist/* /home/c3nav/static/
    gunicorn --bind=0.0.0.0 c3nav.wsgi
else
  python manage.py $@
fi
