import os
from flask import Flask, request, redirect, render_template, url_for, abort, session, send_from_directory, flash, Response
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

print __name__

f = file('mash.cfg')
cfg = Config(f)

logger = logging.getLogger('web')
file_handler = logging.FileHandler('log/web.log')
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.setLevel(logging.DEBUG)

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
session = Session()
logger.debug('Finished setting up db.')

logger.debug('Settingup login manager...')
login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.login_view = 'login'
logger.debug('Finished setting up login manager.')

logger.debug('Setting up principals...')
principals = Principal()
normal_role = RoleNeed('user')
normal_permission = Permission(normal_role)
principals._init_app(app)
logger.debug('Finished setting up principals.')

@login_manager.user_loader
def load_user(id):
	return session.query(User).filter(User.id==id).first()

@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		if authenticate(username, password):
			user = session.query(User).filter(User.nickname==username).first()
			if user is not None:
				login_user(user)
			next_arg = request.args.get('next')
			next = '' if next_arg is None else next_arg
			return redirect(next)
		else:
			return abort(401)
	else:
		return render_template('login.html') 
def authenticate(username, password):
	return True
        
@app.route("/logout")
@login_required
def logout():
	logout_user()
	flash('You have successfully logged out')
	return render_template('logout.html')

def allowed_file(filename):
	return '.' in filename and \
	filename.rsplit('.', 1)[1] in cfg.ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def home():
	if request.method == 'POST':
		try:
			key = uuid.uuid4().hex
			song1 = request.files['song1']
			song1Filename = save_file(song1, key)
			song2 = request.files['song2']
			song2Filename = save_file(song2, key)
			status = 'uploaded'
			userid = 0 if current_user.is_anonymous() else int(current_user.id)
			mash = Mash(key, userid, song1Filename, song2Filename, status)	
			session.add(mash)
			session.commit()
			socket.send_json(convert_mash_to_zeromq_message(mash))
			return redirect(url_for('mash', key=mash.key))
		except Exception, err:
			logger.exception('Something bad happened:')
		finally:
			session.rollback()
	return render_template('index.html')

def convert_mash_to_zeromq_message(mash):
	try:
		obj = [{'id':mash.id, 'key':mash.key, 'song1':mash.song1, 'song2':mash.song2, 'status':mash.status}]
		return json.dumps(obj)
	except Exception, err:
		logger.exception('Something bad happened: convert_mash_to_zeromq_message, mash={0}'.format(mash))

def save_file(file, key):
	try:
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			folder = os.path.join(cfg.UPLOAD_FOLDER, key)
			if not os.path.exists(folder):
				os.makedirs(folder)		
			file.save(os.path.join(cfg.UPLOAD_FOLDER, key, filename))
			return filename
	except Exception, err:
		logger.exception('Something bad happened: save_file, key={0}, filename={1}'.format(key, file.filename))

@app.route('/uploads/<key>/<filename>')
def uploads(key, filename):
	logger.debug('/uploads/{0}/{1}'.format(key, filename))
	folder = os.path.join(cfg.UPLOAD_FOLDER, key)
	return send_from_directory(folder, filename)

@app.route('/mash/<key>')
def mash(key):
	try:
		logger.debug('/mash/{0}'.format(key))
		mash = session.query(Mash).filter(Mash.key==key).first()
		return render_template('mash.html', mash=mash)
	except Exception, err:
		logger.exception('Something bad happened: mash, key={0}'.format(key))

@app.route('/list')
def list():
	try:
		userid = 0 if current_user.is_anonymous() else int(current_user.id)
		mashes = session.query(Mash).filter(User.id == userid)
		return render_template('list.html', mashes=mashes)
	except Exception, err:
		logger.exception('Something bad happened: list')
		
@app.route('/resubmit/<key>')
@login_required
def resubmit(key):
	try:
		userid = 0 if current_user.is_anonymous() else int(current_user.id)
		mash = session.query(Mash).filter(Mash.key==key).filter(Mash.user_id==userid).first()
		socket.send_json(convert_mash_to_zeromq_message(mash))
		return redirect(url_for('mash', key=mash.key))
	except Exception, err:
		logger.exception('Something bad happened: resubmit, key={0}'.format(key))

@app.errorhandler(403)
def page_not_found(e):
	session['redirected_from'] = request.url
	return redirect(url_for('login'))

if __name__ == '__main__':
	app.debug = True
	app.run('0.0.0.0', 8000)
