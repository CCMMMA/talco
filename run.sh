#!/bin/bash

flask db init
flask db migrate -m "Creating databases"
flask db upgrade

uwsgi --ini talco.ini