class Config(object):
	SECRET_KEY = 'IUHWEUHWIUHE@(@(*YWG'
	UPLOAD_FOLDER = 'upload'
 	MASH_FOLDER = 'mash'

class ProdConfig(Config):
	REMOTEPUSH = 'tcp://0.0.0.0:5000'
	SQLALCHEMY_DATABASE_URI = 'sqlite:///mash.db'

class DevConfig(Config):
	ASSETS_DEBUG = True
	DEBUG = True
	SQLALCHEMY_ECHO = True
	REMOTEPUSH = 'tcp://0.0.0.0:5000'
	SQLALCHEMY_DATABASE_URI = 'sqlite:///mash.db'
