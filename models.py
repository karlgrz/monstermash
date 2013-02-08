from flask_sqlalchemy import SQLAlchemy
from monstermash import app

db = SQLAlchemy(app)

class Mash(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	key = db.Column(db.String)
	song1 = db.Column(db.String)
	song2 = db.Column(db.String)
	status = db.Column(db.String)

	def __init__(self, key, song1, song2, status):
		self.key = key
		self.song1 = song1
		self.song2 = song2
		self.status = status

ROLE_USER = 0
ROLE_ADMIN = 1

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	nickname = db.Column(db.String, unique=True)
	email = db.Column(db.String, unique=True)
	role = db.Column(db.SmallInteger, default=ROLE_USER)
	mashes = db.relationship('Mash', backref='user', lazy='dynamic')

	def __init__(self, nickname, email, role, mashes):
		self.nickname = nickname
		self.email = email
		self.role = role
		self.mashes = mashes

	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return unicode(self.id)

	def __repr__(self):
		return '<User {0}>'.format(self.nickname)
