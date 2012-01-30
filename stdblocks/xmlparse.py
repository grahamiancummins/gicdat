#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2008-02-27.

# Copyright (C) 2008 Graham I Cummins
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

from xml.sax.handler import ContentHandler
from xml.sax import make_parser
import gicdat.doc
import StringIO
from gicdat.enc import DOT

class QuickHandler(ContentHandler):
	def __init__(self):
		ContentHandler.__init__(self)
		self.elements=[]

	def startElement(self, name, attrs):
		#print "open %s -  %s" % (name, str(dict(attrs)))
		ob={'_tag':name, '_els':[], '_cdata':[]}
		ob.update(dict(attrs))
		if self.elements:
			self.elements[-1]['_els'].append(ob)
		self.elements.append(ob)	
		
	def characters(self, characters):
		'''characters(str) =>None
If self.object.cdata is a string, append charaters to it'''
		self.elements[-1]['_cdata'].append(characters)

	def endElement(self, name):
		'''name(str) => None
if self.tag==name, call cleanUp, then change the handler back self.handler'''
		#print "close %s" % name
		self.elements[-1]['_cdata']=''.join(self.elements[-1]['_cdata'])
		if len(self.elements)>1:
			self.elements.pop()

def quickRead(stream):
	'''
	Returns an XML document tree made of simple dicts. These dicts have special
	keys _tag: string containing the xml tag, _els: list containing child
	elements, and _cdata: string containing the cdata
	
	'''
	sp = make_parser()
	ch =  QuickHandler()
	sp.setContentHandler(ch)
	sp.parse(stream)
	return ch.elements[0]

def quickSearch(d, tag, depth=-1, heads = True):
	'''
	Tag searching for dict structures (as returned by quickRead)
	returns a list of all elements (as dicts) that are children of d out to
	depth "depth" (use a negative value for unlimited depth), and the have tag
	"tag".

	'''
	hits = []
	if d['_tag'] == tag:
		hits.append(d)
		if heads:
			return hits
	if depth == 0:
		return hits
	for e in d['_els']:
		hits.extend(quickSearch(e, tag, depth-1, heads))
	return hits

def tagSearch(d, n, tag, depth=-1):
	'''
	Tag searching for PatchDict structures (as returned by readStream).

	return a list of all keys in d that point to elements which have the
	element at key n in their chain of containers, and which have tag
	"tag". This assumes "child" links in elements of d. 

	'''
	hits = []
	if d[n]['tag'] == tag:
		hits.append(n)
	if depth == 0:
		return hits
	for lk in d[n]['links']:
		l = d[n]['links'][lk]
		if l['tag'] == 'child':
			hits.extend(tagSearch(d, l['targ'], tag, depth-1))
	return hits

def readStream(stream, keepdoc=True):
	'''
	returns a tree structure for the document (this is a PatchDict).
	
	'link' determines how to represent the xml parent/child relationships. If
	'c' is in the string link, then parent elements will have link dictionaries
	with tag "child" added for each contained element. If 'p' is in the string,
	then child elements will have a link with tag "parent" pointing to their
	container. (you can use "pc" for both, and "" for neither).	

	if keepdoc is False, then the top level element in the document is
	discarded. If the only use for this element is as a container for
	subelements that constitute the document's data, then this may be a good
	thing.	
	
	'''
	d = quickRead(stream) 
	pd = gicdat.doc.Doc()
	if keepdoc:
		toD(d, '', pd)
	else:
		for e in d['_els']:
			toD(e, '', pd)
	return pd

def xmlname(d):
	'''
	Determine a base name for an XML element d and return it (a string).
	This function looks for an attribute "Name" or "name" and if it finds one,
	uses that. Otherwise, it uses the element's tag

	'''
	n = d.get('Name') or d.get('name') or d['_tag']
	n = n.replace('.', DOT)
	return n

def toD(d, n, pd):
	'''
	recursively add xml element d and any contained elements to pd. The main
	comuputation is to add keys to pd by side-effect. "n" specifies the name of
	the parent element of d (as a key in pd), if there is one. If not, n should
	be an empty string. 

	'''
	name = pd.ukey(n +xmlname(d))
	if d['_cdata'].strip():
		pd[name] = d['_cdata']
	val = {}
	for k in d:
		if not k in ['_tag', '_cdata', '_els']:
			pd[name + '.'+ k.replace('.', DOT)] = d[k] 
	pd[name + '.tag'] = d['_tag']
	for e in d['_els']:
		toD(e, str(name) + ".", pd)

def readFile(fn, keepdoc=True):
	'''Thin wrapper around readStream that opens a file named fn'''
	f = open(fn)
	return readStream(f, keepdoc)
	
def readString(s, keepdoc=True):
	'''Thin wrapper around readStream using StringIO'''
	f = StringIO.StringIO(s)
	return readStream(f, keepdoc)
