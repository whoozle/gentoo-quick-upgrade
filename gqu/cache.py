import cPickle
import os
import time

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
		with open(self.get_path(name)) as f:
			return cPickle.load(f)

	def save_file(self, name, obj):
		with open(self.get_path(name), 'wb') as f:
			cPickle.dump(obj, f)
