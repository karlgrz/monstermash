from flask_sqlalchemy import SQLAlchemy
from web import app

db = SQLAlchemy(app)

class Mash(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	song1 = db.Column(db.String)
	song2 = db.Column(db.String)
	url = db.Column(db.String)

	def __init__(self, song1, song2, url):
		self.song1 = song1
		self.song2 = song2
		self.url = url
