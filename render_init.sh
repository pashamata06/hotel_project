#!/bin/bash
python manage.py migrate
python manage.py shell -c "from hotel.management.commands.initdb import run; run()"
