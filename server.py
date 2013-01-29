#!/usr/bin/env python
# encoding: utf=8

import zmq
import json
import time
from afromb import AfromB 
from filedownloader import FileDownloader
from mashmessage import MashMessage

context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.bind('tcp://0.0.0.0:5000')

while True:
	message = socket.recv_json()
	obj = json.loads(message)[0]
	mash = MashMessage(obj['id'], obj['key'], obj['song1'], obj['song2'], obj['status'])
	
	song1 = FileDownloader(mash.song1)
	song1.download()

	song2 = FileDownloader(mash.song2)
	song2.download()

	print 'KEY={0},SONG1={1},SONG2={2},STATUS={3}'.format(mash.key, mash.song1, mash.song2, mash.status)
	tic = time.time()
	afromb = AfromB(mash.song1, mash.song2, 'output.mp3', ).run(mix='0.9', envelope='env')
	toc = time.time()
	print "Elapsed time: %.3f sec" % float(toc-tic)
