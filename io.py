#!/usr/bin/env python -3
# encoding: utf-8

#Created by gic on DATE.

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

import StringIO, os
from doc import Doc, EXTERN
from urlparse import urlparse
import blocks, search

def subdocs(doc):
	'''
	Return a list of the externalDocuments in doc that specify separate file
	information (e.g., they are Doc instances and their "url" is set to a
	non-empty value). Each subdoc in the list is represented as a 4-list. The
	first element is the key in Doc that represents the location of the
	externalDocument in doc, the second is the url of the doc, the third is the
	filetype (which may be inferred by the "getFiletype" function),  and the
	last is a Doc instance that contains only the nodes that are associated to
	the particular subdoc.

	The return value is always at least length 1, with the first tuple
	representing the main doucemnt. If there are subdocs, the last element of
	this first line will not be the same as the main doc, since some nodes will
	be removed. The "name" of the first element is ""

	return [ [name, url, filetype, nodes], ....]

	'''
	docs = [['', doc['_url'], doc['_filetype'], doc]]
	sds = doc.findall(EXTERN, tops = True)
	if not sds:
		return docs
	doc = doc.copy()
	docs[0][-1] = doc
	for ns in sds:
		sd = doc[ns]
		url = sd['_extern_url']
		ft = sd['_filetype'] or guesstype(url)
		sd['_url'] = url
		sd['_filetype'] = ft
		doc[ns] = Doc({'_extern_url':url, '_filetype':ft })
		docs.extend(subdocs(sd))
	return docs

def getfiletype(doc, url=None):
	'''
	Return a mimetype-like string representing the filetype of doc. This uses the resolution order:
	doc.filetype, if it is set (and not "unknown")
	guesstype(url) if url is passed in
	guesstype(doc.url) if that is set
	'''
	ft = guesstype(url or doc.url)
	if ft == "unknown" and doc['_filetype']:
		ft = doc['_filetype']
	return ft
	
def gethandler(filetype, mode='r'):
	'''
	Return a gicdat.Parser subclass that claims it can handle files of filetype (a mimetype-like string) in mode ('r' or 'w' for read or write)

	'''
	for p in blocks.parsers():
		if mode == 'r' and filetype in p.canread:
			return p
		elif mode == 'w' and filetype in p.canwrite:
			return p
	raise IOError('No known handler for file type %s in mode %s' % (filetype, mode))

def guesstype(url):
	'''
	Return a filetype associated to the url "url"
	'''
	path = urlparse(url).path
	ext = os.path.splitext(path)[-1].lstrip('.')
	for p in blocks.parsers():
		if ext in p.extensions:
			return p.extensions[ext]
	return 'unknown'	

def openurl(url, mode = 'r', filetype=None):
	'''
	Open a stream attached to "url" in mode (r or w)
	'''
	p = urlparse(url, 'file')
	if p.scheme == 'file':
		return open(p.path, mode + 'b')
	schemes = blocks.urlschemes()
	for s in schemes:
		if mode == 'r' and  p.scheme in s.canread:
			return s.open(url, 'r', filetype)
		elif mode == 'w' and p.scheme in s.canwrite:
			return s.open(url, 'w', filetype)
	raise IOError('No known handler for url scheme %s in mode %s' % (p.scheme, mode))

def _kwget(k, d, default=None, remove=True):
	'''
	Return a value associated to key k in dictionary d. If the value is not in
	d, return default. If remove is True, then if the key was in d, delete it
	
	'''
	v = default
	if k in d:
		v = d[k]
		if remove:
			del(d[k])
	return v

def read(url, **kw):
	'''
	Read a document at url. Returns a gicdat.doc.Doc (or raises IOError)
	
	kw arguments may include:

	'filetype': str  - use the specified filetype (rather than trying to guess
	from the url)

	'''
	ft = _kwget('filetype', kw) or guesstype(url)
	stream = openurl(url, 'r')
	d = readstream(stream, ft, url=url, **kw)
	stream.close()
	return d

def readstream(stream, filetype, **kw):
	'''
	Get a Doc instance by reading the file-like object f which has type
	filetype
	
	'''
	url = _kwget('url', kw, None)
	parser = gethandler(filetype, 'r')
	d, code = parser.read(stream, filetype, **kw)
	#should be an "allNodes" dict, and a list of 3-tuples (name, url, filetype)
	if code:
		blocks.register(code)
	d['_url'] = url
	d['_filetype'] = filetype
	if kw.get('subdocs'):
		sds  = subdocs(d)
		for sd in sds[1:]:
			d.attach(sd[0], read(sd[1], filetype=sd[2], **kw))
	return d

def readstring(s, filetype):
	sio = StringIO.StringIO(s)
	d = readstream(sio)
	sio.close()
	return d

def write(doc, url, **kw):
	'''
	Write doc to url. Returns None.
	kw arguments may include:

	'subdocs':bool  - If not True, don't split off subdocuments that say they
	should be saved to separate urls.

	'filetype': str - Force writing a file of that type
	'''
	ft = _kwget('filetype', kw) or getfiletype( doc, url )
	doc['_url'] = url
	doc['_filetype'] = ft
	if not kw.get('subdocs'):
		sds = [('', url, ft, doc)]
	else:
		sds = subdocs(doc)
		sds[0] = ('', url, ft, sds[0][-1])
	for d in sds:
		name, url, ft, doc = d
		stream = openurl(url, 'w', ft)
		parser = gethandler(ft, 'w')
		parser.write(doc, stream, ft, **kw)
		stream.close()

def writestream(doc, f, filetype, **kw):
	parser = gethandler(filetype, 'w')
	parser.write(doc, f, filetype **kw)

def writestring(doc, filetype, **kw):
	sio = StringIO.StringIO()
	writestream(doc, sio, **kw)
	s = sio.getvalue()
	sio.close()
	return s

