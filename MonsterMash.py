#!/usr/bin/env python
# encoding: utf=8

import zmq
import json
import requests
import time
from afromb import AfromB 

context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.bind('tcp://0.0.0.0:5000')

class MashMessage:
	def __init__(self, id, song1, song2, url):
		self.id = id
		self.song1 = song1
		self.song2 = song2
		self.url = url

while True:
	message = socket.recv_json()
	obj = json.loads(message)[0]
	mash = MashMessage(obj['id'], obj['song1'], obj['song2'], obj['url'])
	
	print 'Downloading song1={0}'.format(mash.song1)
	r = requests.get('http://127.0.0.1:8000/uploads/{0}'.format(mash.song1))
	with open(mash.song1, "wb") as song:
		song.write(r.content)

	print 'Downloading song2={0}'.format(mash.song2)
	r = requests.get('http://127.0.0.1:8000/uploads/{0}'.format(mash.song2))
	with open(mash.song2, "wb") as song:
		song.write(r.content)

	print 'ID={0},SONG1={1},SONG2={2},URL={3}'.format(mash.id, mash.song1, mash.song2, mash.url)
	tic = time.time()
	afromb = AfromB(mash.song1, mash.song2, 'output.mp3', ).run(mix='0.9', envelope='env')
	toc = time.time()
	print "Elapsed time: %.3f sec" % float(toc-tic)
