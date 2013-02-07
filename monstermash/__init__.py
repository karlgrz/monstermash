import os
from flask import Flask 
from werkzeug import secure_filename
from flask.ext.assets import Environment
from webassets.loaders import PythonLoader as PythonAssetsLoader
from config import Config
import assets
import zmq
import json
import logging
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

print __name__

f = file('mash.cfg')
cfg = Config(f)

for key in cfg:
	print '{0} : {1}'.format(key, cfg[key])

logger = logging.getLogger('web')
handler = logging.FileHandler('./log/web.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

for key in cfg:
	logger.debug('{0} : {1}'.format(key, cfg[key]))

app = Flask(__name__)
app.secret_key = cfg.SECRET_KEY

context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.connect(cfg.REMOTEPUSH)

assets_env = Environment(app)
assets_loader = PythonAssetsLoader(assets)
for name, bundle in assets_loader.load_bundles().iteritems():
	assets_env.register(name, bundle)

from modelsserver import *

db = create_engine(cfg.SQLALCHEMY_DATABASE_URI)
db.echo = True
Session = sessionmaker(bind=db)
session = Session()

import monstermash.views
