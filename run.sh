#!/bin/bash

flask db init
flask db migrate -m "Creating databases"
flask db upgrade

flask run --host=0.0.0.0 --port=8080