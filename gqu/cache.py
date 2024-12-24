import pickle
import os
import sys
import logging
import time

log = logging.getLogger("cache")

class Cache(object):
	Expiration = 24 * 3600

	def __init__(self, path):
		self.path = path
		if not os.path.exists(path):
			os.makedirs(path)

	def get_path(self, name):
		return os.path.join(self.path, name.replace('/', '-'))

	def valid_file(self, name):
		path = self.get_path(name)
		return os.path.exists(path) and time.time() - os.stat(path).st_mtime < Cache.Expiration

	def load_file(self, name):
		if not self.valid_file(name):
			return None
		try:
			with open(self.get_path(name), "rb") as f:
				return pickle.load(f)
		except:
			log.error("failed opening cache", exc_info=sys.exc_info())

	def save_file(self, name, obj):
		with open(self.get_path(name), 'wb') as f:
			pickle.dump(obj, f)
