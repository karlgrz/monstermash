#!/usr/bin/env python
# encoding: utf=8

import zmq
import json
import time
from afromb import AfromB 
from filedownloader import FileDownloader
from mashmessage import MashMessage
import subprocess
import os
from config import Config
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from modelsserver import *
import logging

logger = logging.getLogger('server')
file_handler = logging.FileHandler('log/server.log')
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.setLevel(logging.DEBUG)

f = file('mash.cfg')
cfg = Config(f)

context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.bind(cfg.localmq)

temp = cfg.temp
uploadFolder = cfg.uploadFolder
remotehost = cfg.remotehost
dbhost = cfg.dbhost

logger.debug('localmq={0}'.format(cfg.localmq))
logger.debug('temp={0}'.format(cfg.temp))
logger.debug('uploadFolder={0}'.format(cfg.uploadFolder))
logger.debug('remotehost={0}'.format(cfg.remotehost))
logger.debug('dbhost={0}'.format(cfg.dbhost))

db = create_engine(dbhost)
db.echo = True 
Session = sessionmaker(bind=db)
session = Session()

while True:
	message = socket.recv_json()
	obj = json.loads(message)[0]
	mash = MashMessage(obj['id'], obj['key'], obj['song1'], obj['song2'], obj['status'])
	try:	
		logger.debug('Processing: (id={0},key={1},song1={2},song2={3},status={4})'.format(mash.id, mash.key, mash.song1, mash.song2, mash.status))
		song1 = FileDownloader(remotehost, temp, mash.key, mash.song1)
		song1.download()

		song2 = FileDownloader(remotehost, temp, mash.key, mash.song2)
		song2.download()

		mashoutput = '{0}/{1}/{2}'.format(temp, mash.key, 'output.mp3')

		logger.debug('KEY={0},SONG1={1},SONG2={2},STATUS={3},OUTPUT={4}'.format(mash.key, song1.output, song2.output, mash.status, mashoutput))

		tic = time.time()
		afromb = AfromB(song1.output, song2.output, mashoutput).run(mix='0.9', envelope='env')
		toc = time.time()
		logger.debug("Elapsed time: %.3f sec" % float(toc-tic))

		outputpath = os.path.join(uploadFolder, mash.key, 'output.mp3')	
		p = subprocess.Popen(["scp", mashoutput, "{0}@{1}:{2}".format(cfg.outputhostuser, cfg.outputhostname, outputpath)])
		sts = os.waitpid(p.pid, 0)

		mashupdate = session.query(Mash).filter(Mash.id==mash.id).first()
		mashupdate.status = 'ready'
		session.commit()
	except Exception, err :
		mashupdate = session.query(Mash).filter(Mash.id==mash.id).first()
		mashupdate.status = 'failed'
		mashupdate.error = err
		session.commit()
		logger.exception('Something failed processing key={0}:'.format(mash.key))
