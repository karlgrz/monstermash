import os
from flask import Flask, request, redirect, render_template, url_for, abort, session, send_from_directory, flash, Response
import uuid
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug import secure_filename
#from flask.ext.assets import Environment
#from webassets.loaders import PythonLoader as PythonAssetsLoader
#from config import Config
#import assets
#import zmq
import json
#import logging
#from sqlalchemy import *
#from sqlalchemy.orm import sessionmaker
from flask.ext.principal import identity_changed, current_app, Identity, AnonymousIdentity, RoleNeed, UserNeed, identity_loaded
from __init__ import app, logger, db, db_session, login_manager, cfg, socket, admin_permission
from models import *

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
				login_user(user)
				identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
			next_arg = request.args.get('next')
			next = '' if next_arg is None else next_arg
			return redirect(next or '/')
		else:
			return abort(401)
	else:
		return render_template('login.html') 

def authenticate(username, password):
	user = db_session.query(User).filter(User.username==username).first()
	return user.password == password
        
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
		mash = db_session.query(Mash).filter(Mash.key==key).first()
		return render_template('mash.html', mash=mash)
	except Exception, err:
		logger.exception('Something bad happened: mash, key={0}'.format(key))

@app.route('/list')
@admin_permission.require(http_exception=403)
def list():
	try:
		mashes = db_session.query(Mash)
		return render_template('list.html', mashes=mashes)
	except Exception, err:
		logger.exception('Something bad happened: list')
		
@app.route('/resubmit/<key>')
@admin_permission.require(http_exception=403)
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

@app.errorhandler(403)
def page_not_found(e):
	session['redirected_from'] = request.url
	return redirect(url_for('login'))
