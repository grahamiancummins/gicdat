#!/usr/bin/env python -3
# encoding: utf-8

#Created by gic on Sun Oct 24 13:45:51 CDT 2010

# Copyright (C) 2010 Graham I Cummins
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA 02111-1307 USA
#
from __future__ import print_function, unicode_literals

from gicdat.base import Parser
import gicdat.doc, gicdat.enc
import numpy, os
import zipfile, StringIO



class GD1Parse(Parser):
	'''	
	This parser handles gicdat's internal file format, which is a form of zip
	file. This is for the second alpha version (now depricated).

	'''
	
	canread = ('application/com.symbolscope.gicdat.legacy',)
	extensions = {'gic1':'application/com.symbolscope.gicdat.legacy'}

	def read(self, stream, filetype, **kw):
		z = zipfile.ZipFile(stream, 'r')
		rdat = z.read('data.raw')
		dd = eval(z.read('doc.py'))
		gicdat.enc.dictcleanup(dd)
		doc = gicdat.enc.dict2doc(dd, rdat)
		return (doc, None)

	

class GicParse(Parser):
	'''	
	This parser handles gicdat's internal file format, which is a form of zip
	file

	'''
	
	canread = ('application/com.symbolscope.gicdat',)
	canwrite = ('application/com.symbolscope.gicdat',)
	extensions = {'gic':'application/com.symbolscope.gicdat'}

	def read(self, stream, filetype, **kw):
		z = zipfile.ZipFile(stream, 'r')
		rdat = z.read('data.raw')
		dd = eval(z.read('doc.py'))
		doc = gicdat.enc.dict2doc(dd, rdat, False)
		return (doc, None)
	
	def write(self, d, stream, filetype, **kw):
		z = zipfile.ZipFile(stream, 'w')
		dstr = StringIO.StringIO()
		d = gicdat.enc.doc2dict(d, dstr)
		z.writestr('doc.py', repr(d))
		z.writestr('data.raw', dstr.getvalue())
		dstr.close()	


	
class GicLogParse(Parser):
	canread = ('application/com.symbolscope.gicdatlog',)
	extensions = {'giclog':'application/com.symbolscope.gicdatlog'}

	def read(self, stream, filetype, **kw):
		s = stream.read()
		if not s.endswith('}'):
			s = s + "}"
		d = eval(s)
		d = gicdat.doc.Doc(d)
		return (d, None)	
	

giclog_p = GicLogParse()

class LoggedDoc(gicdat.doc.Doc):
	def __init__(self, arg=None, fname='log.giclog', memcopy=True):
		self.fname = fname
		self.memcopy = memcopy
		self.logging = False
		gicdat.doc.Doc.__init__(self)
		if os.path.isfile(fname):
			d = giclog_p.read(open(fname, 'r'), None)[0]
			self.update(d)
			self.update(gicdat.doc.Doc(arg))
		else:
			gicdat.doc.Doc.__init__(self, arg)
		self.file = open(fname, 'w')
		self.file.write("{")
		for k in self.keys():
			self.log(k, self[k])
		self.logging = True
		
	def fulldoc(self):
		if self.memcopy:
			return gicdat.doc.Doc(self)
		else:
			self.file.flush()
			d = giclog_p.read(open(self.fname, 'r'), None)[0]
			return d
		
	def rdel(self, k):
		dict.__delitem__(self, k)
		
	def pfnkey(self, pf, k):
		if k.startswith(pf):
			try:
				n = int(k[len(pf):])
				return n
			except:
				pass
		return -1
		
	def pfnkeys(self, pf):
		keys = []
		ns = []
		for k in self.keys():
			n = self.pfnkey(pf, k)
			if n > -1:
				keys.append(k)
				ns.append(n)
		return [keys[i] for i in numpy.argsort(numpy.array(ns))]
	
	def limit(self, pf, n):
		k = self.pfnkeys(pf)
		while len(k)>n:
			dk = k.pop(0)
			self.rdel(dk)
		
	def set(self, k, v, safe=True, unique=False, fast=False):
		if self.logging:
			self.log(k, v)
			if self.memcopy:
				gicdat.doc.Doc.set(self, k, v, safe, unique, fast)
		else:
			gicdat.doc.Doc.set(self, k, v, safe, unique, fast)
		
	def writeval(self, k , v):
		if gicdat.doc.search.classify(v) == "#":
			v = gicdat.doc.search.astuple(v)
		self.file.write('"%s":' % k)
		self.file.write(repr(v))
		self.file.write(",")
		self.file.flush()
		
	def log(self, k, v):
		if isinstance(v, gicdat.doc.Doc):
			for sk in v.keys(-1, subdockeys=False):
				sv = v[sk]
				self.writeval(k+'.'+sk, sv)
		else:
			self.writeval(k, v)
		
class JSONParse(Parser):
	'''
	This parser handles JSON serialization, using base64 encoding for the data
	content of arrays

	'''

	canread= ('application/json',)
	canwrite = ('application/json',)
	extensions = {'json':'application/json'}

	def read(self, stream, filetype, **kw):
		''' 
		Ignores filetype (since only one is supported, so we always know what it is), and kw (since there are no special behaviors). 
		'''
		doc = gicdat.enc.fromjson(stream)
		return (doc, None)	
	
	def write(self, d, stream, filetype, *kw):
		gicdat.enc.tojson(d, stream)

oldgic_p = GD1Parse()
gic_p = GicParse()
json_p = JSONParse()


