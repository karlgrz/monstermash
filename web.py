import os
from flask import Flask, render_template, request, redirect, url_for, abort, session, send_from_directory
from werkzeug import secure_filename
from flask.ext.assets import Environment
from webassets.loaders import PythonLoader as PythonAssetsLoader
import assets
import zmq
import json
import uuid
import logging
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger('web')
handler = logging.FileHandler('./log/web.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

ALLOWED_EXTENSIONS = set(['mp3'])
env = os.environ.get('FLASK_ENV', 'prod')
app = Flask(__name__)
app.config.from_object('settings.%sConfig' % env.capitalize())
app.config['ENV'] = env

logger.info('app.config[REMOTEPUSH] = {0}'.format(app.config['REMOTEPUSH']))

context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.connect(app.config['REMOTEPUSH'])

assets_env = Environment(app)
assets_loader = PythonAssetsLoader(assets)
for name, bundle in assets_loader.load_bundles().iteritems():
	assets_env.register(name, bundle)

from modelsserver import *

db = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
db.echo = True
Session = sessionmaker(bind=db)
session = Session()

def allowed_file(filename):
	return '.' in filename and \
	filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

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
			mash = Mash(key, song1Filename, song2Filename, status)	
			mashupdate = session.query(Mash).filter(Mash.id==mash.id).first()
			session.add(mash)
			session.commit()
			socket.send_json(convert_mash_to_zeromq_message(mash))
			return redirect(url_for('mash', key=mash.key))
		except Exception as ex:
			session.rollback()
			logger.error('Something bad happened:', ex)
	return render_template('index.html')

def convert_mash_to_zeromq_message(mash):
	try:
		obj = [{'id':mash.id, 'key':mash.key, 'song1':mash.song1, 'song2':mash.song2, 'status':mash.status}]
		return json.dumps(obj)
	except Exception as ex:
		logger.error('Something bad happened: convert_mash_to_zeromq_message, mash={0}'.format(mash), ex)

def save_file(file, key):
	try:
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			folder = os.path.join(app.config['UPLOAD_FOLDER'], key)
			if not os.path.exists(folder):
				os.makedirs(folder)		
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], key, filename))
			return filename
	except Exception as ex:
		logger.error('Something bad happened: save_file, key={0}, filename={1}'.format(key, file.filename), ex)

@app.route('/uploads/<key>/<filename>')
def uploads(key, filename):
	print '/uploads/{0}/{1}'.format(key, filename)
	folder = os.path.join(app.config['UPLOAD_FOLDER'], key)
	return send_from_directory(folder, filename)

@app.route('/mash/<key>')
def mash(key):
	try:
		print '/mash/{0}'.format(key)
		mash = session.query(Mash).filter(Mash.key==key).first()
		return render_template('mash.html', mash=mash)
	except Exception as ex:
		logger.error('Something bad happened: mash, key={0}'.format(key), ex)

@app.route('/list')
def list():
	try:
		mashes = session.query(Mash).all()
		return render_template('list.html', mashes=mashes)
	except Exception as ex:
		logger.error('Something bad happened: list', ex)
		
@app.route('/resubmit/<key>')
def resubmit(key):
	try:
		mash = session.query(Mash).filter(Mash.key==key).first()
		socket.send_json(convert_mash_to_zeromq_message(mash))
		return redirect(url_for('mash', key=mash.key))
	except Exception as ex:
		logger.error('Something bad happened: resubmit, key={0}'.format(key), ex)
		
if __name__ == '__main__':
	app.debug = True
	app.run('0.0.0.0', 8000)
