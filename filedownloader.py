#!/usr/bin/env python
# encoding: utf=8

import requests

class FileDownloader:
	def __init__(self, filename):
		self.filename = filename
	def download(self):
		print 'Downloading file={0}'.format(self.filename)
		r = requests.get('http://127.0.0.1:8000/uploads/{0}'.format(self.filename))
		with open(self.filename, "wb") as file:
			file.write(r.content)
