import os
import json


basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    with open(os.path.join(basedir, 'config.json')) as config_file:
        config_data = json.load(config_file)

    SECRET_KEY = config_data.get('SECRET_KEY', 'password')
    SQLALCHEMY_DATABASE_URI = config_data.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///' + os.path.join(basedir, 'app.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = config_data.get('SQLALCHEMY_TRACK_MODIFICATIONS', False)

    WCM3_URL = config_data.get('WCM3_URL')
    hours = config_data.get('hours', 168)
    delta_lat = config_data.get('delta_lat', 0.0013659036107000276)
    delta_long = config_data.get('delta_long', 0.0017988219935232432)
    wcm3_min_lat = config_data.get('wcm3_min_lat', 39.8)
    wcm3_min_long = config_data.get('wcm3_min_long', 13.1)
    species = config_data.get('species', [])
    bacteria = config_data.get('bacteria', [])
