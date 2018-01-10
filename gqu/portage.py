import os
import re
from gqu.version import Version
from gqu.cache import Cache
import logging
import subprocess

log = logging.getLogger('portage')

class Portage(object):
	def __init__(self, args):
		self.args = args
		self.config_dir = os.path.expanduser('~/.gentoo-quick-upgrade')
		self.cache = Cache(self.config_dir)

		self.installed = {}
		self.available = {}
		self.read()

	def load_file(self, name):
		if self.args.sync:
			return None
		return self.cache.load_file(name)

	def save_file(self, name, obj):
		return self.cache.save_file(name, obj)

	def read(self):
		self.installed = self.read_installed_packages()
		self.available.update(self.read_packages('/usr/portage'))
		self.available.update(self.read_packages('/var/lib/layman'))

	def read_installed_packages(self):
		installed = self.load_file('installed')
		if installed:
			return installed

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
		cache = 'available' + root
		available = self.cache.load_file(cache)
		if available:
			return available

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
