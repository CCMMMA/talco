import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'password'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    WCM3_URL = 'http://193.205.230.6/opendap/wcm3/d03/archive/'
    hours = 168
    delta_lat = 0.0013659036107000276
    delta_long = 0.0017988219935232432
    wcm3_min_lat = 39.8
    wcm3_min_long = 13.1
