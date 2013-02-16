from sqlalchemy import *
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Mash(Base):
	__tablename__ = 'mash'

	id = Column(Integer, primary_key=True)
	key = Column(String(32))
	user_id = Column(Integer, ForeignKey('user.id'))
	song1 = Column(String(255))
	song2 = Column(String(255))
	status = Column(String(32))
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
	username = Column(String(32), unique=True)
	password = Column(String(40))
	salt = Column(String(32))
	role = Column(SmallInteger, default=ROLE_USER)
	mashes = relationship('Mash')

	def __init__(self, username, password, salt, role):
		self.username = username
		self.password = password
		self.salt = salt
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

