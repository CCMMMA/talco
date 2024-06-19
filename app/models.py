from app import db


class Measurements(db.Model):
    __tablename__ = 'measurements'
    id = db.Column(db.String(32), primary_key=True)
    year = db.Column(db.Integer)
    date = db.Column(db.Date)
    site_code = db.Column(db.Integer, db.ForeignKey('farms.site_code'))
    site_name = db.Column(db.String(128))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    animal = db.Column(db.String(128))
    outcome = db.Column(db.Integer)
    bacteria = db.Column(db.String(64))
    unit = db.Column(db.String(16))
    to_consider = db.Column(db.Boolean, default=False, nullable=False)
    farm = db.relationship('Farms', backref='measurement', uselist=False)
    timeseries = db.relationship('Timeseries', uselist=False)


class Farms(db.Model):
    __tablename__ = 'farms'
    site_code = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    bbox = db.Column(db.JSON)
    coordinates = db.Column(db.JSON)


class Timeseries(db.Model):
    __tablename__ = 'timeseries'
    id = db.Column(db.String(32), db.ForeignKey('measurements.id'), primary_key=True)
    values = db.Column(db.JSON)
