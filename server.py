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

f = file('mash.cfg')
cfg = Config(f)

context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.bind(cfg.localmq)

temp = cfg.temp
uploadFolder = cfg.uploadFolder
remotehost = cfg.remotehost
print cfg.localmq
print temp
print uploadFolder
print remotehost

while True:
	message = socket.recv_json()
	obj = json.loads(message)[0]
	mash = MashMessage(obj['id'], obj['key'], obj['song1'], obj['song2'], obj['status'])
	
	song1 = FileDownloader(remotehost, temp, mash.key, mash.song1)
	song1.download()

	song2 = FileDownloader(remotehost, temp, mash.key, mash.song2)
	song2.download()

	mashoutput = '{0}/{1}/{2}'.format(temp, mash.key, 'output.mp3')

	print 'KEY={0},SONG1={1},SONG2={2},STATUS={3},OUTPUT={4}'.format(mash.key, song1.output, song2.output, mash.status, mashoutput)

	tic = time.time()
	afromb = AfromB(song1.output, song2.output, mashoutput).run(mix='0.9', envelope='env')
	toc = time.time()
	print "Elapsed time: %.3f sec" % float(toc-tic)

	outputpath = os.path.join(uploadFolder, mash.key, 'output.mp3')	
	p = subprocess.Popen(["scp", mashoutput, "{0}@{1}:{2}".format(cfg.outputhostuser, cfg.outputhostname, outputpath)])
	sts = os.waitpid(p.pid, 0)
