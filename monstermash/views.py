import os
from flask import Flask, request, redirect, render_template, url_for, abort, session, send_from_directory, flash, Response, g
import uuid
from werkzeug import secure_filename
import json
from __init__ import app, logger, cfg, socket
from models import *
from pagination import Pagination
import hashlib
import rethinkdb as r

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
			userid = 0
			mash = Mash(key, userid, song1Filename, song2Filename, status)	
			r.db('monstermash').table('mashes').insert(mash).run(g.rdb_conn)
			socket.send_json(convert_mash_to_zeromq_message(mash))
			return redirect(url_for('mash', key=mash.key))
		except Exception, err:
			logger.exception('Something bad happened:')
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
			folder = os.path.join(app.root_path, cfg.UPLOAD_FOLDER, key)
			if not os.path.exists(folder):
				os.makedirs(folder)		
			file.save(os.path.join(folder, filename))
			return filename
	except Exception, err:
		logger.exception('Something bad happened: save_file, key={0}, filename={1}'.format(key, file.filename))

@app.route('/uploads/<key>/<filename>')
def uploads(key, filename):
	logger.debug('/uploads/{0}/{1}'.format(key, filename))
	folder = os.path.join(app.root_path, cfg.UPLOAD_FOLDER, key)
	logger.debug('folder={0}, filename={1}'.format(folder, filename))
	return send_from_directory(folder, filename)

@app.route('/mash/<key>')
def mash(key):
	try:
		logger.debug('/mash/{0}'.format(key))
		mash = r.db('monstermash').table('mashes').get(key).run(g.rdb_conn)
		return render_template('mash.html', mash=mash)
	except Exception, err:
		logger.exception('Something bad happened: mash, key={0}'.format(key))

PER_PAGE = 5 

@app.route('/list/', defaults = {'page':1})
@app.route('/list/page/<int:page>')
def list(page = 1):
	try:
		items = r.db('monstermash').table('mashes')
		count = items.count().run(g.rdb_conn)
		logger.debug('list: page={0}'.format(page))
		mashes = items.skip(PER_PAGE * (page - 1)).limit(PER_PAGE)
		if not mashes and page != 1:
			abort(404)
		pagination = Pagination(page, PER_PAGE, count)
		return render_template('list.html', pagination=pagination, mashes=mashes)
	except Exception, err:
		logger.exception('Something bad happened: list')

@app.route('/resubmit/<key>')
def resubmit(key):
	try:
		mash = r.db('monstermash').table('mashes').get(key).run(g.rdb_conn)
		socket.send_json(convert_mash_to_zeromq_message(mash))
		return redirect(url_for('mash', key=mash.key))
	except Exception, err:
		logger.exception('Something bad happened: resubmit, key={0}'.format(key))

@app.route('/about')
def about():
	logger.debug('IN ABOUT')
	return render_template('about.html')

@app.route('/rethinkdb/<id>')
def rethinkdb(id):
	items = r.db('test').table('items')
	items.insert({"id": id, "value": "value" }).run(g.rdb_conn)
	count = items.count().run(g.rdb_conn)
	all_items = items.run(g.rdb_conn)
	return render_template('rethinkdb.html', count=count, items=all_items) 

@app.errorhandler(403)
def page_not_found(e):
	session['redirected_from'] = request.url
	return redirect(url_for('login'))
