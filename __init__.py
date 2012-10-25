from flask import Flask, render_template, request, redirect, url_for, abort, session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'HGEJKH@&ASA<&@(!!H'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'

from models import *

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/new', methods=['POST'])
def new():
	url = 'test-url'
	mash = Mash (request.form['song1'], request.form['song2'], url)
	db.session.add(mash)
	db.session.commit()
	return redirect(url_for('mash', mashId=mash.id))

@app.route('/mash/<mashId>')
def list(mashId):
	mash = Mash.query.filter_by(id=mashId).first_or_404()
	return render_template('mash.html', mash=mash)

if __name__ == '__main__':
	app.debug = True
	app.run()
