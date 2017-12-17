from application import db
import datetime

class Placement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(128), index=False, unique=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    x = db.Column(db.Integer)
    y = db.Column(db.Integer)

    def __init__(self, user, x, y):
        self.user = user
        self.x = x
        self.y = y

    def __repr__(self):
        return '<User %r><Timestamp %r><Coord %r,%r>' % (self.user, self.timestamp, self.x, self.y)

class Representation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bitmap = db.Column(db.String(256), index=False, unique=False)

    def __init__(self, bitmap):
        self.bitmap = bitmap

    def __repr__(self):
        return '<Bitmap %r>' % self.bitmap

class User(db.Model):
    user_id = db.Column(db.String(128), primary_key=True)
    name = db.Column(db.String(128), index=False, unique=False)
    family_name = db.Column(db.String(128), index=False, unique=False)
    given_name = db.Column(db.String(128), index=False, unique=False)
    picture = db.Column(db.String(256), index=False, unique=False)
    email = db.Column(db.String(128), index=False, unique=False)
    locale = db.Column(db.String(32), index=False, unique=False)
    nextPlacementEligibleAt = db.Column(db.Integer, index=False, unique=False, default=0)
    banned = db.Column(db.Boolean, index=False, unique=False, default=False)

    def __init__(self, name, given_name, family_name, user_id, email, picture, locale):
        self.name = name
        self.family_name = family_name
        self.given_name = given_name
        self.picture = picture
        self.user_id = user_id
        self.email = email
        self.locale = locale

    def __repr__(self):
        return '<name %r> <userID %r> <nextPlacementEligibleAt %r> <banned %r>' % (self.name, self.user_id, self.nextPlacementEligibleAt, self.banned)
