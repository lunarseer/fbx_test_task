#!/usr/bin/sh
pip install -r requirements.txt
export FLASK_APP=app:app
export FLASK_DEBUG=1
flask run