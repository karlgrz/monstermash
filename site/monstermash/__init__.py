import os
from flask import Flask, request, redirect, render_template, url_for, abort, session, send_from_directory, flash, Response, g
import uuid
from werkzeug import secure_filename
from flask.ext.assets import Environment
from webassets.loaders import PythonLoader as PythonAssetsLoader
from config import Config
import assets
import json
import logging
import zmq
from rethinkdbclient import RethinkDBClient

f = file('mash.cfg')
cfg = Config(f)

logger = logging.getLogger('web')
file_handler = logging.FileHandler('log/web.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logger.setLevel(logging.DEBUG)

logger.debug(__name__)

for key in cfg:
	logger.debug('{0} : {1}'.format(key, cfg[key]))

app = Flask(__name__)
app.secret_key = cfg.SECRET_KEY

logger.debug('Setting up zmq...')
context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.connect(cfg.REMOTEPUSH)
logger.debug('Finished setting up zmq.')

logger.debug('Setting up assets_env...')
assets_env = Environment(app)
assets_loader = PythonAssetsLoader(assets)
for name, bundle in assets_loader.load_bundles().iteritems():
	assets_env.register(name, bundle)
logger.debug('Finished setting up assets_env.')

rdb_client = RethinkDBClient(cfg.RETHINKDB, 'monstermash')

from views import *
