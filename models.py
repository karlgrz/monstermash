from sqlalchemy import *
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Mash(Base):
	__tablename__ = 'mash'

	id = Column(Integer, primary_key=True)
	key = Column(String)
	user_id = Column(String, ForeignKey('user.id'))
	song1 = Column(String)
	song2 = Column(String)
	status = Column(String)
	user = relationship('User')

	def __init__(self, key, user_id, song1, song2, status):
		self.key = key
		self.user_id = user_id
		self.song1 = song1
		self.song2 = song2
		self.status = status
	
	def __repr__(self):
		return "<Mash('{0}','{1}','{2}','{3}','{4}')>".format(self.key,self.user_id,self.song1,self.song2,self.status)

ROLE_USER = 0
ROLE_ADMIN = 1

class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key=True)
	username = Column(String, unique=True)
	email = Column(String, unique=True)
	role = Column(SmallInteger, default=ROLE_USER)
	mashes = relationship('Mash')

	def __init__(self, username, email, role):
		self.username = username
		self.email = email
		self.role = role

	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return unicode(self.id)

	def __repr__(self):
		return '<User {0}>'.format(self.username)

