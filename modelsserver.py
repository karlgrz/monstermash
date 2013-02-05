from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Mash(Base):
	__tablename__ = 'mash'

	id = Column(Integer, primary_key=True)
	key = Column(String)
	song1 = Column(String)
	song2 = Column(String)
	status = Column(String)

	def __init__(self, key, song1, song2, status):
		self.key = key
		self.song1 = song1
		self.song2 = song2
		self.status = status
	
	def __repr__(self):
		return "<Mash('{0}','{1}','{2}','{3}')>".format(self.key,self.song1,self.song2,self.status)
