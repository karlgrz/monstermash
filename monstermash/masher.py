#!/usr/bin/env python
# encoding: utf=8

"""
masher.py

mash song A and song B together

By Karl Grzeszczak 2013-03-26

Mash together two songs with sox
"""
import numpy
import sys
import os
import time
from mediainfo import MediaInfo
import subprocess

usage="""
Usage:
	python masher.py <inputfilenameA> <inputfilenameB> <outputfilename>

Example:
	python masher.py BillieJean.mp3 CryMeARiver.mp3 BillieJeanFromCryMeARiver.mp3

"""

class Masher(object):
	def __init__(self, input_filename_a, input_filename_b, output_filename):
		self.input_a = input_filename_a
		self.input_b = input_filename_b
		self.output_filename = output_filename

	def run(self):
		p = subprocess.Popen(["sox", "-m", "{0}".format(self.input_a), "{0}".format(self.input_b), "{0}".format(self.output_filename), "norm"])
		sts = os.waitpid(p.pid, 0)
				
def main():
	try:
		input_filename_a = sys.argv[1]
		input_filename_b = sys.argv[2]
		output_filename = sys.argv[3]
	except:
		print usage
		sys.exit(-1)
	Masher(input_filename_a, input_filename_b, output_filename).run()

if __name__=='__main__':
	tic = time.time()
	main()
	toc = time.time()
	print "Elapsed time: %.3f sec" % float(toc-tic)
