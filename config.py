import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database


# local db
# SQLALCHEMY_DATABASE_URI = 'postgresql://jcarcamo:hola1234@192.168.0.80:5432/fyyur_db'
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:example@localhost:5432/fyyur_db'

