import os
from flask import Flask, render_template, request, redirect, url_for, abort, session, send_from_directory
from werkzeug import secure_filename
from flask.ext.assets import Environment
from webassets.loaders import PythonLoader as PythonAssetsLoader
import assets
import zmq
import json
import uuid

context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.connect('tcp://0.0.0.0:5000')

ALLOWED_EXTENSIONS = set(['mp3'])
env = os.environ.get('FLASK_ENV', 'prod')
app = Flask(__name__)
app.config.from_object('settings.%sConfig' % env.capitalize())
app.config['ENV'] = env

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
		song1Filename = save_file(song1)
		song2 = request.files['song2']
		song2Filename = save_file(song2)
		mash = Mash(key, song1Filename, song2Filename, 'uploaded')	
		db.session.add(mash)
		db.session.commit()
		socket.send_json(convert_mash_to_zeromq_message(mash))
		return redirect(url_for('mash', mashId=mash.id))
	return render_template('index.html')

def convert_mash_to_zeromq_message(mash):
	obj = [{'id':mash.id, 'key':mash.key, 'song1':mash.song1, 'song2':mash.song2, 'status':mash.status}]
	return json.dumps(obj)

def save_file(file):
	if file and allowed_file(file.filename):
		filename = secure_filename(file.filename)
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		return filename

@app.route('/uploads/<filename>')
def uploaded_file(filename):
	return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/mash/<mashId>')
def mash(mashId):
	mash = Mash.query.filter_by(id=mashId).first_or_404()
	return render_template('mash.html', mash=mash)

@app.route('/list')
def list():
	mashes = Mash.query.all()
	return render_template('list.html', mashes=mashes)

@app.route('/resubmit/<mashId>')
def resubmit(mashId):
	mash = Mash.query.filter_by(id=mashId).first_or_404()
	socket.send_json(convert_mash_to_zeromq_message(mash))
	return redirect(url_for('mash', mashId=mash.id))
	
if __name__ == '__main__':
	app.debug = True
	app.run('0.0.0.0', 8000)
