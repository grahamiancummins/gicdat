#!/usr/bin/env python 
# encoding: utf-8

#Created by Graham Cummins on Jun 6, 2011

# Copyright (C) 2011 Graham I Cummins
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later 
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT 
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS 
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA 02111-1307 USA
#

from __future__ import print_function  #, unicode_literals
#unicode literals generates strange urllib errors
import jobs
import json
from control import report
import doc as gd
from rest import Resource


'''
Goal: It should be possible to send a job for evaluation, and get back the
results as quickly as possible. It should also be possible to send a job for
asynchronous evaluation, providing a callback mechanism to run when the
result is returned. Jobs consist of Transform subclasses, a small Document
instance that specifies parameters to the Transform, and a large Document
that specifies source data. The backend performing the Transform needs to
support being 1) in a different process, 2) Written in a different language,
or 3) running on a different machine. Efficiency and safety are the primary
objectives.

Challenges: 
Documents may be very large. Some Transforms may be very
expensive, and others may be fast. Some sensible workflows might include an
expensive transform that operates on a large Document, producing a small
change, followed by several faster transforms that use the modified Document.
Transmitting the whole large Document across a net connection (or even to
another process) for each small transform is inefficient, thus, the remote
system should have some way to maintain the state of a Document. However, the
remote system can't mutate a Document freely, since there may be asynchronous
processes that need to use the old version. This implies that the remote
system needs to store versions of documents.

Since remote systems may not all be the same, allowing individual transforms
to produce new remote document versions is a bookkeeping nightmare, since a
sequence of two transforms might then only be valid if they happen to be sent
to the same execution backend.

Documents are most useful if they have complex types. However, complex types,
and mutable types in particular make the problem of sending Documents to
remote systems and quickly comparing them much more difficult.

Specification:

Main server:



'''


AUTH = [None, None, None]

vl = str('http://van-lorax.vancouver.wsu.edu/gd')
lh = str('http://localhost:4242')


def auth(realm, uname, passwd):
	AUTH[0] = realm
	AUTH[1] = uname
	AUTH[2] = passwd

class GDDocServ(Resource):
	def __init__(self, url, authrealm = None, uname=None, passwd =None):
		Resource.__init__(self,url, authrealm, uname, passwd, 'application/json')
	
	def idof(self, s):
		try:
			id = json.loads(s)['id']
		except:
			raise NameError("No doc ID in response %s" % s)
		return id
	
	def isok(self, s):
		try:
			ok = json.loads(s)['ok']
			if ok:
				return True
		except:
			pass
		return False	
	
	def adddoc(self, doc):
		s = jobs.d2str(doc)
		try:
			r = self.put('/doc', s, ctype=jobs.CTYPE)
		except:
			raise
		return self.idof(r)
	
	def addjob(self, job, prs):
		js = jobs.d2str(job.todoc())
		url = '/job'
		for i, p in enumerate(prs):
			if i:
				url =url+"&inp=%i" % p
			else:
				url = url+"?inp=%i" % p
		r = self.put(url, js, ctype=jobs.CTYPE)
		return self.idof(r)
	
	def collect(self, ret, delete, pref='j'):
		d = gd.Doc()
		for i, id in enumerate(ret):
			di = self.get('/doc/%i' % id, ctype=jobs.CTYPE)
			try:
				di = jobs.str2d(di)
			except:
				raise ValueError('No document in response %s' % di)
			d['%s%i' % (pref, i)] = di
		if delete:
			url = "/doc?" + "&".join(["id=%i" % i for i in delete])
			z = self.delete(url)
			if not self.isok(z):
				report("WARNING: delete failed: %s" % z)
		return d
		
	
	def do_incr(self, seq, doc):
		js, prs, ret = seq
		if not prs:
			prs = [[-1]] * len(js)
		doc = jobs.subset(doc, js, prs)
		did = self.adddoc(doc)
		jids = []
		for i, j in enumerate(js):
			pr = [jids[x] for x in prs[i] if x>=0]
			if -1 in prs[i]:
				pr = [did]+pr
			jids.append(self.addjob(j, pr))
		if ret!=None:
			ret = [jids[r] for r in ret]
		else:
			ret = jids
		r = self.collect(ret, [did]+jids, 'j')
		return r
	
	def do(self, seq, doc):
		js, prs, ret = seq
		d = gd.Doc()
		d['inp'] = doc
		d['prs'] = prs
		d['ret'] = ret
		for i in range(len(js)):
			d['j%i' % i] = js[i].todoc()
		r = self.put('/seq', jobs.d2str(d), 'application/zip', 
					{'Accept':'application/zip'} )
		try:
			return jobs.str2d(r)
		except:
			print(r)

def eval(seq, doc, serv):
	rs = GDDocServ(serv)
	rs.rsock=None
	return  rs.do(seq, doc)
		
