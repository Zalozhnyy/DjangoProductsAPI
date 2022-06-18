#!/bin/bash

python manage.py migrate wait
echo migrations complete
python manage.py runserver 0.0.0.0:8000
