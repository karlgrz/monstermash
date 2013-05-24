import os
from flask import Flask, request, redirect, render_template, url_for, abort, session, send_from_directory, flash, Response, g
import uuid
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug import secure_filename
import json
from flask.ext.principal import identity_changed, current_app, Identity, AnonymousIdentity, RoleNeed, UserNeed, identity_loaded
from __init__ import app, logger, db, db_session, login_manager, cfg, socket, admin_permission
from models import *
from pagination import Pagination
import hashlib
import rethinkdb as r

@login_manager.user_loader
def load_user(id):
	return db_session.query(User).filter(User.id==id).first()

@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		if authenticate(username, password):
			user = db_session.query(User).filter(User.username==username).first()
			if user is not None:
				logger.debug('Successfully logged in user: {0}'.format(username))
				login_user(user)
				identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
			next_arg = request.args.get('next')
			next = '' if next_arg is None else next_arg
			return redirect(next or '/')
		else:
			logger.error('User: {0} failed to login.'.format(username))
			return abort(401)
	else:
		return render_template('login.html') 

def authenticate(username, password):
	user = db_session.query(User).filter(User.username==username).first()
	if user is None:
		return False
	else:		
		hashed_password = hashlib.sha512(password + user.salt).hexdigest()
		return user.password == hashed_password

@app.route('/register', methods=["GET", "POST"])
def register():
	if request.method == 'POST':
		try:
			username = request.form['username']
			password = request.form['password']
		
			user = db_session.query(User).filter(User.username==username).first()
			if user is None:
				salt = uuid.uuid4().hex        
				hashed_password = hashlib.sha512(password + salt).hexdigest()
				new_user = User(username, hashed_password, salt, ROLE_USER)
				db_session.add(new_user)
				db_session.commit()
				return render_template('login.html')
			else:
				logger.debug('Username already exists. Try again.')
				abort(404)
		except Exception, err:
			logger.exception('Something bad happened: /register')
		finally:
			db_session.rollback()
	return render_template('register.html')

@app.route("/logout")
@login_required
def logout():
	logout_user()
	for key in ('identity.name', 'identity.auth_type'):
		session.pop(key, None)
	
	identity_changed.send(current_app._get_current_object(), 
						  identity=AnonymousIdentity())

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
			db_session.add(mash)
			db_session.commit()
			socket.send_json(convert_mash_to_zeromq_message(mash))
			return redirect(url_for('mash', key=mash.key))
		except Exception, err:
			logger.exception('Something bad happened:')
		finally:
			db_session.rollback()
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
		mash = db_session.query(Mash).filter(Mash.key==key).first()
		return render_template('mash.html', mash=mash)
	except Exception, err:
		logger.exception('Something bad happened: mash, key={0}'.format(key))

PER_PAGE = 5 

@app.route('/list/', defaults = {'page':1})
@app.route('/list/page/<int:page>')
def list(page = 1):
	try:
		count = db_session.query(Mash).count()
		logger.debug('list: page={0}'.format(page))
		mashes = db_session.query(Mash).offset(PER_PAGE * (page - 1)).limit(PER_PAGE)
		if not mashes and page != 1:
			abort(404)
		pagination = Pagination(page, PER_PAGE, count)
		return render_template('list.html', pagination=pagination, mashes=mashes)
	except Exception, err:
		logger.exception('Something bad happened: list')

@app.route('/resubmit/<key>')
def resubmit(key):
	try:
		mash = db_session.query(Mash).filter(Mash.key==key).first()
		socket.send_json(convert_mash_to_zeromq_message(mash))
		return redirect(url_for('mash', key=mash.key))
	except Exception, err:
		logger.exception('Something bad happened: resubmit, key={0}'.format(key))

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
	identity.user = current_user

	if hasattr(current_user, 'id'):
		identity.provides.add(UserNeed(current_user.id))

	if hasattr(current_user, 'role'):
		identity.provides.add(RoleNeed(current_user.role))

@app.route('/about')
def about():
	logger.debug('IN ABOUT')
	return render_template('about.html')

@app.route('/rethinkdb/<id>')
def rethinkdb(id):
	items = r.db('test').table('items')
	items.insert({"id": id, "value": "value" }).run(g.rdb_conn)
	count = items.count().run(g.rdb_conn)
	return render_template('rethinkdb.html', count = count)

@app.errorhandler(403)
def page_not_found(e):
	session['redirected_from'] = request.url
	return redirect(url_for('login'))
