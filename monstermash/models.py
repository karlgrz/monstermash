class Mash():

	def __init__(self, key, user_id, song1, song2, status):
		self.key = key
		self.user_id = user_id
		self.song1 = song1
		self.song2 = song2
		self.status = status
	
	def __repr__(self):
		return "<Mash('{0}','{1}','{2}','{3}','{4}')>".format(self.key,self.user_id,self.song1,self.song2,self.status)
