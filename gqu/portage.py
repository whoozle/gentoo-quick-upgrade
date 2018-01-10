import os
import re
from gqu.version import Version
import time
import logging
import subprocess
import cPickle

log = logging.getLogger('portage')

class Portage(object):
	Expiration = 24 * 3600

	def __init__(self, args):
		self.args = args
		self.config_dir = os.path.expanduser('~/.gentoo-quick-upgrade')
		if not os.path.exists(self.config_dir):
			os.mkdir(self.config_dir)

		self.installed = {}
		self.available = {}
		self.read()

	def config_path(self, name):
		return os.path.join(self.config_dir, name)

	def valid_file(self, name):
		if self.args.sync:
			return False
		path = self.config_path(name)
		return os.path.exists(path) and time.time() - os.stat(path).st_mtime < Portage.Expiration

	def load_file(self, name):
		with open(self.config_path(name)) as f:
			return cPickle.load(f)

	def save_file(self, name, obj):
		with open(self.config_path(name), 'wb') as f:
			cPickle.dump(obj, f)

	def read(self):
		self.installed = self.read_installed_packages()
		self.available.update(self.read_packages('/usr/portage'))
		self.available.update(self.read_packages('/var/lib/layman'))

	def read_installed_packages(self):
		if self.valid_file('installed'):
			return self.load_file('installed')

		log.info('reading installed packages')
		out = subprocess.check_output(['equery', 'list', '*'], bufsize=32768)
		installed = {}
		for atom in out.split('\n'):
			atom = atom.strip()
			if not atom:
				continue
			try:
				package, version = self.parse_atom(atom)
				installed[package] = version
			except:
				raise
				log.warning('invalid package atom %s' %atom)
		log.info('read %d installed packages' %len(installed))
		self.save_file('installed', installed)
		return installed

	atom_re = re.compile(r'^(.*?)-([\.\d]+.*)$')

	def parse_atom(self, atom):
		m = Portage.atom_re.match(atom)
		if not m:
			raise Exception('invalid atom %s' %atom)
		return m.group(1), Version(m.group(2))

	def read_packages(self, root):
		cache = 'available' + root.replace('/', '-')
		if self.valid_file(cache):
			return self.load_file(cache)

		log.info('reading portage data...')
		available = {}
		for dirpath, dirs, files in os.walk(root, topdown=False):
			dir = os.path.relpath(dirpath, root)
			atom = '/'.join(dir.split('/')[-2:])
			if atom[0] == '.':
				continue

			versions = []
			for file in files:
				if file.endswith('.ebuild'):
					try:
						name, _ext = os.path.splitext(file)
						_name, version = self.parse_atom(name)
						versions.append(version)
					except:
						log.warning('invalid package atom %s' %atom)
			if versions:
				available[atom] = versions

		log.info('read %d packages from %s' %(len(available), dirpath))
		self.save_file(cache, available)
		return available

	def upgrade(self):
		log.info('calculating upgrade...')
		packages = []
		for atom, installed_version in self.installed.iteritems():
			if atom in self.available:
				versions = self.available[atom]
				for version in versions:
					if version.dev:
						continue
					if version > installed_version:
						log.info('upgrade available for %s: %s' %(atom, version))
						packages.append(atom)
						break
			else:
				log.warning('unavailable package %s' %atom)
		log.info('done')
		print 'sudo emerge --keep-going=y -v1a %s' % ' '.join(packages)
