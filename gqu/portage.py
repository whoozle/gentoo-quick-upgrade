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
		self.available.update(self.read_packages())

	def read_installed_packages(self):
		installed = self.load_file('installed')
		if installed:
			return installed

		log.info('reading installed packages')
		installed = {}
		for dirpath, dirs, files in os.walk('/var/db/pkg'):
			if 'PF' not in files:
				continue
			with open(os.path.join(dirpath, 'SLOT')) as f:
				slot = f.read().strip()
			with open(os.path.join(dirpath, 'CATEGORY')) as f:
				cat = f.read().strip()
			with open(os.path.join(dirpath, 'PF')) as f:
				pf = f.read().strip()
			atom = cat + '/' + pf
			try:
				package, version = self.parse_atom(atom)
				installed[package, slot] = version
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

	def read_packages(self):
		cache = 'available'
		available = self.load_file(cache)
		if available:
			return available

		log.info('reading portage data...')
		available = {}
		process = subprocess.Popen(['equery', 'list', '-p', '-F', '$cp $slot $version', '*'], stdout=subprocess.PIPE, bufsize=1024 * 128)
		while True:
			line = process.stdout.readline().strip()
			if line != b'':
				atom, slot, version = line.split()
				versions = available.setdefault((atom, slot), [])
				versions.append(Version(version))
			else:
				break

		log.info('read %d packages' %(len(available)))
		self.save_file(cache, available)
		return available

	def upgrade(self):
		log.info('calculating upgrade...')
		packages = []
		for (atom, slot), installed_version in self.installed.iteritems():
			key = (atom, slot)
			if key in self.available:
				versions = self.available[key]
				for version in versions:
					if version.dev:
						continue
					if version > installed_version:
						log.info('upgrade available for %s: %s -> %s' %(atom, installed_version, version))
						packages.append(atom)
						break
			else:
				log.warning('unavailable package %s' %atom)
		log.info('done')
		print 'sudo emerge --keep-going=y -v1a %s' % ' '.join(packages)
