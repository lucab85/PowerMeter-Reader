#!/usr/bin/python
# coding: utf-8
# Copyright 2017 Luca Berton
__author__ = 'lucab85'

import os
import json
import logging.config
from settings import PATH_LOGGING

class logmanagement():
	logobj = None
	@classmethod
	def getlog(cls, classname, loggername, forceloggername=False):
		if cls.logobj == None:
			cls.logobj = logmanagement(classname, loggername)

		if forceloggername is True and cls.logobj.loggername != loggername:
			cls.logobj = logmanagement(classname, loggername)

		cls.logobj.log.debug('Log Management %s => %s' % (classname, cls.logobj.loggername))
		return cls.logobj

	def __init__(self, classname, loggername):
		self.setup_logging()
		self.classname = classname
		self.loggername = loggername
		self.log = logging.getLogger(loggername)

	def setup_logging(self, default_path=PATH_LOGGING, default_level=logging.INFO, env_key='LOG_CFG'):
		path = default_path
		self.logconf = None
		value = os.getenv(env_key, None)
		if value:
			path = value
		if os.path.exists(path):
			with open(path, 'rt') as f:
				config = json.load(f)
			self.logconf = logging.config.dictConfig(config)
		elif os.path.exists(path.replace("../", "")):
			with open(path.replace("../", ""), 'rt') as f:
				config = json.load(f)
				self._changePath(config["handlers"])
			self.logconf = logging.config.dictConfig(config)
		else:
			print("Configurazione log non trovata (\"%s\"): applico le impostazioni predefinite" % path)
			self.logconf = logging.basicConfig(level=default_level)

	def _changePath(dictionary):
		for k1, v1 in dictionary.iteritems():
			if type(v1) is dict:
				for k2 in v1.keys():
					if k2 == "filename":
						original = dictionary[k1][k2]
						replaced = original.replace("../", "")
						dictionary[k1][k2] = replaced

	def getLogger(self):
		return self.log

