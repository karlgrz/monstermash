import os
from flask import Flask, render_template, request, redirect, url_for, abort, session, send_from_directory
from werkzeug import secure_filename
from flask.ext.assets import Environment
from webassets.loaders import PythonLoader as PythonAssetsLoader
import assets
import zmq
import json
import uuid

ALLOWED_EXTENSIONS = set(['mp3'])
env = os.environ.get('FLASK_ENV', 'prod')
app = Flask(__name__)
app.config.from_object('settings.%sConfig' % env.capitalize())
app.config['ENV'] = env

print app.config['REMOTEPUSH']

context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.connect(app.config['REMOTEPUSH'])

assets_env = Environment(app)
assets_loader = PythonAssetsLoader(assets)
for name, bundle in assets_loader.load_bundles().iteritems():
	assets_env.register(name, bundle)

from models import *

def allowed_file(filename):
	return '.' in filename and \
	filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def home():
	if request.method == 'POST':
		key = uuid.uuid4().hex
		song1 = request.files['song1']
		song1Filename = save_file(song1, key)
		song2 = request.files['song2']
		song2Filename = save_file(song2, key)
		status = 'uploaded'
		mash = Mash(key, song1Filename, song2Filename, status)	
		db.session.add(mash)
		db.session.commit()
		socket.send_json(convert_mash_to_zeromq_message(mash))
		return redirect(url_for('mash', key=mash.key))
	return render_template('index.html')

def convert_mash_to_zeromq_message(mash):
	obj = [{'id':mash.id, 'key':mash.key, 'song1':mash.song1, 'song2':mash.song2, 'status':mash.status}]
	return json.dumps(obj)

def save_file(file, key):
	if file and allowed_file(file.filename):
		filename = secure_filename(file.filename)
		folder = os.path.join(app.config['UPLOAD_FOLDER'], key)
		if not os.path.exists(folder):
			os.makedirs(folder)		
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], key, filename))
		return filename

@app.route('/uploads/<key>/<filename>')
def uploads(key, filename):
	print '/uploads/{0}/{1}'.format(key, filename)
	folder = os.path.join(app.config['UPLOAD_FOLDER'], key)
	return send_from_directory(folder, filename)

@app.route('/mash/<key>')
def mash(key):
	print '/mash/{0}'.format(key)
	mash = Mash.query.filter_by(key=key).first_or_404()
	return render_template('mash.html', mash=mash)

@app.route('/list')
def list():
	mashes = Mash.query.all()
	return render_template('list.html', mashes=mashes)

@app.route('/resubmit/<key>')
def resubmit(key):
	mash = Mash.query.filter_by(key=key).first_or_404()
	socket.send_json(convert_mash_to_zeromq_message(mash))
	return redirect(url_for('mash', key=mash.key))
	
if __name__ == '__main__':
	app.debug = True
	app.run('0.0.0.0', 8000)
