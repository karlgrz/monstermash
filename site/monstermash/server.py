#!/usr/bin/env python
# encoding: utf=8

import zmq
import json
import time
from masher import Masher
from filedownloader import FileDownloader
from mashmessage import MashMessage
import subprocess
import pwd
import grp
import os
from config import Config
import logging
from rethinkdbclient import RethinkDBClient

logger = logging.getLogger('server')
file_handler = logging.FileHandler('log/server.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
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

temp_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), temp)
logger.debug('temp_folder:{0}'.format(temp_folder))

while True:
	message = socket.recv_json()
	logger.debug('message: {0}'.format(message))
	obj = json.loads(message)[0]
	logger.debug('obj: {0}'.format(obj))
	mash = MashMessage(obj['id'], obj['key'], obj['song1'], obj['song2'], obj['status'])
	logger.debug('mash: {0}'.format(mash))
	try:
		try:
			logger.debug('Processing: (id={0},key={1},song1={2},song2={3},status={4})'.format(mash.id, mash.key, mash.song1, mash.song2, mash.status))
			song1 = FileDownloader(remotehost, temp_folder, mash.key, mash.song1)
			song1.download()

			song2 = FileDownloader(remotehost, temp_folder, mash.key, mash.song2)
			song2.download()

			mashoutput = '{0}/{1}/{2}'.format(temp_folder, mash.key, 'output.mp3')

			logger.debug('KEY={0},SONG1={1},SONG2={2},STATUS={3},OUTPUT={4}'.format(mash.key, song1.output, song2.output, mash.status, mashoutput))

			tic = time.time()
			masher = Masher('{0}'.format(song1.output), '{0}'.format(song2.output), mashoutput).run()
			toc = time.time()
			logger.debug("Elapsed time: %.3f sec" % float(toc-tic))

			outputpath = os.path.join(uploadFolder, mash.key, 'output.mp3')
			if (cfg.outputhostname == 'localhost'):
				scp_output = outputpath
			else:
				scp_output = '{0}@{1}:{2}'.format(cfg.outputhostuser, cfg.outputhostname, outputpath)

			logger.debug("Starting scp {0} {1}".format(mashoutput, scp_output))
			p = subprocess.Popen(["scp", mashoutput, scp_output])
			sts = os.waitpid(p.pid, 0)

			if (cfg.outputhostname == 'localhost'):
				uid = pwd.getpwnam(cfg.outputhostuser).pw_uid
				gid = grp.getgrnam(cfg.outputhostuser).gr_gid
				os.chown(outputpath, uid, gid)
			logger.debug("sts={0}".format(sts))
			rdb_client = RethinkDBClient(cfg.RETHINKDB, 'monstermash')
			rdb_client.update('mashes', mash.key, {'status' : 'ready'})
		except Exception, err :
			logger.exception('Something failed processing key={0}:'.format(mash.key))
			rdb_client = RethinkDBClient(cfg.RETHINKDB, 'monstermash')
			rdb_client.update('mashes', mash.key, {'status' : 'failed', 'error' : err})
	finally:
		if (rdb_client):
			rdb_client.close()
