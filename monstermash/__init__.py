import os
from flask import Flask, request, redirect, render_template, url_for, abort, session, send_from_directory, flash, Response, g
import uuid
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
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
from flask.ext.principal import Principal, RoleNeed, Permission 
import rethinkdb as r

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

from models import *

logger.debug('Setting up db...')
db = create_engine(cfg.SQLALCHEMY_DATABASE_URI)
db.echo = True
Session = sessionmaker(bind=db)
db_session = Session()
logger.debug('Finished setting up db.')

logger.debug('Settingup login manager...')
login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.login_view = 'login'
logger.debug('Finished setting up login manager.')

logger.debug('Setting up principals...')
principals = Principal()
user_role = RoleNeed(ROLE_USER)
user_permission = Permission(user_role)
admin_role = RoleNeed(ROLE_ADMIN)
admin_permission = Permission(admin_role)
principals._init_app(app)

logger.debug('Finished setting up principals.')

@app.before_request
def before_request():
    try:
        g.rdb_conn = r.connect(host=cfg.RETHINKDB, port='28015', db='test')
    except RqlDriverError:
        abort(503, "No database connection could be established.")

@app.teardown_request
def teardown_request(exception):
    try:
        g.rdb_conn.close()
    except AttributeError:
        pass

from views import *
