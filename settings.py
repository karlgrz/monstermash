class Config(object):
	SECRET_KEY = 'IUHWEUHWIUHE@(@(*YWG'
	UPLOAD_FOLDER = 'upload'
 	MASH_FOLDER = 'mash'


class ProdConfig(Config):
	SQLALCHEMY_DATABASE_URI = 'sqlite:///mash.db'

class DevConfig(Config):
	ASSETS_DEBUG = True
	DEBUG = True
	SQLALCHEMY_DATABASE_URI = 'sqlite:///mash.db'
	SQLALCHEMY_ECHO = True
