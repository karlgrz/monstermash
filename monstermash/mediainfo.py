#!/usr/bin/env python
# encoding: utf=8

"""
song_info.py

capture ffmpeg output of a file

By Karl Grzeszczak 2013-03-27

"""
import sys
import subprocess

class MediaInfo(object):
	def __init__(self, input_filename):
		self.input = input_filename

	def inspect(self):
		p = subprocess.Popen(["ffmpeg", "-i",  self.input])
		print p

