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

context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.bind('tcp://0.0.0.0:5000')

mashTemp = 'mash-temp'
uploadFolder = '~/workspace/monstermash/upload'

remotehost = 'http://127.0.0.1:8000'
while True:
	message = socket.recv_json()
	obj = json.loads(message)[0]
	mash = MashMessage(obj['id'], obj['key'], obj['song1'], obj['song2'], obj['status'])
	
	song1 = FileDownloader(remotehost, mashTemp, mash.key, mash.song1)
	song1.download()

	song2 = FileDownloader(remotehost, mashTemp, mash.key, mash.song2)
	song2.download()

	mashoutput = '{0}/{1}/{2}'.format(mashTemp, mash.key, 'output.mp3')

	print 'KEY={0},SONG1={1},SONG2={2},STATUS={3},OUTPUT{4}'.format(mash.key, song1.output, song2.output, mash.status, mashoutput)

	tic = time.time()
	afromb = AfromB(song1.output, song2.output, mashoutput, ).run(mix='0.9', envelope='env')
	toc = time.time()
	print "Elapsed time: %.3f sec" % float(toc-tic)

	outputpath = os.path.join(uploadFolder, mash.key, 'output.mp3')	
	p = subprocess.Popen(["scp", mashoutput, "karl@localhost:{0}".format(outputpath)])
	sts = os.waitpid(p.pid, 0)
