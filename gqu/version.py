import re

class Version(object):
	ver_re = re.compile(r'\d+')
	dev_re = re.compile(r'^9999+$')
	def __init__(self, text):
		self.text = text
		self.version = []
		self.dev = False
		for m in Version.ver_re.finditer(text):
			v = m.group(0)
			if Version.dev_re.match(v):
				self.dev = True
			self.version.append(int(v))

	def __str__(self):
		return 'version(%s)' %self.text

	def __cmp__(self, o):
		return cmp(self.version, o.version)
