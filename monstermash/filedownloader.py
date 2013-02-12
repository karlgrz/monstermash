#!/usr/bin/env python
# encoding: utf=8

import requests
import os

class FileDownloader:
	def __init__(self, remotehost, base, key, filename):
		self.remotehost = remotehost
		self.base = base
		self.key = key
		self.filename = filename
		self.folder = os.path.join(base, key)
		self.output = os.path.join(self.folder, filename)
	def download(self):
		print 'Downloading file={0}'.format(self.filename)
		if not os.path.exists(self.folder):
			os.makedirs(self.folder)	
		r = requests.get('{0}/uploads/{1}/{2}'.format(self.remotehost, self.key, self.filename))
		with open(self.output, "wb") as file:
			file.write(r.content)
