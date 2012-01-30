#!/usr/bin/env python
# encoding: utf-8

#Created by Graham Cummins on Jun 10, 2011

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

#from __future__ import print_function, unicode_literals
#wsgi requires strings, not unicode
import sys, json
import gicdat.fstore as fstore
CTYPE = 'application/zip'
PORT = 4242

if __name__=='__main__':
	for d in sys.path[:]:
		if d.endswith('/gicdat'):
			sys.path.remove(d)

import gicdat.jobs as gdjs
from traceback import format_exc
from cgi import parse_qs


def do_sequence(s):
	d = gdjs.str2d(s)
	doc = d['inp']
	prs = d['prs']
	ret = d['ret']
	js = [None] * len(prs)
	for k in d:
		if k.startswith('j'):
			i = int(k[1:])
			js[i] = gdjs.Job(d[k]['t'], d[k]['p'], d[k]['o'])
	d= gdjs.distribute_sequence( (js, prs, ret), doc )
	return gdjs.d2str(d)
	

def wstart():
	import os
	scrpt = os.path.join(os.environ['HOME'], 'bin', 'gdworkers')
	log = os.path.join(os.environ['HOME'], '.gicdat', 'gdworklog.log')
	r = os.system(scrpt+' 1 > ' + log)
	return r

def readinput(environ):
	f = environ['wsgi.input']
	l = int(environ.get('CONTENT_LENGTH', 0))
	return f.read(l)

def application(environ, start_response):
	rmeth = environ['REQUEST_METHOD']
	p=environ['PATH_INFO'].strip('/').split('/')
	ctype='application/json'
	try:
		if p[0] == 'doc':
			if rmeth == 'GET':
				if len(p) == 1:
					resp = json.dumps({'ids':fstore.allids([fstore.DOC])})
				else:
					resp = fstore.getdoc(int(p[1]), True)
					ctype = CTYPE
			elif rmeth == 'PUT':
				id = fstore.adddoc(readinput(environ))
				resp = json.dumps({'id':id})
			elif rmeth == 'DELETE':
				pars = parse_qs(environ['QUERY_STRING'])
				ids = [int(i) for i in pars['id']]
				fstore.deldocs(ids)
				resp = json.dumps({'ok':1})
		elif p[0] == 'seq':
			resp = do_sequence(readinput(environ))
			ctype = CTYPE
		elif p[0] == 'clear':
			fstore.rebuild()
			resp = json.dumps({'ok':1})
		elif p[0] == 'dir':
			resp = str(fstore.DIR)
			ctype='text/plain'
		elif p[0] == 'stop':
			fstore.closeworkers()
			resp = json.dumps({'ok':1})
		elif p[0] == 'start':
			r = wstart()
			resp = json.dumps({'ok':r})
		elif p[0] == 'job':
			pars = parse_qs(environ['QUERY_STRING'])
			pr = [int(i) for i in pars['inp']]
			d = readinput(environ)
			ids = fstore.addjobs([d], [pr])
			resp = json.dumps({'id':ids[0]})
		elif p[0] == 'environ':
			resp = json.dumps(dict([(k, str(environ[k])) for k in environ]))
		else:
			resp = 'this is the toplevel of a gicdat remote eval server'
			ctype = 'text/plain'
	except Exception as e:
		resp = json.dumps({'failed':format_exc(e)})
	start_response('200 OK', [('Content-Type', ctype)], [resp])
	return resp

def startserver(port=PORT):
	from wsgiref.simple_server import make_server
	httpd = make_server('', port, application)
	print("Serving on port %i..." % port)
	httpd.serve_forever()

if __name__ == '__main__':
	startserver(PORT)

