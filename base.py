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
import inspect, search

''' 
This module defines template classes that should be used for building extension blocks. None of the classes here can be used directly

Note that classes Tag and Structure in module gicdat.tag, and classes
Visualizer, Control, Show from gicdat.gui.blocks are also GDBlock subclasses,
and can be used as base classes for extensions 

''' 

class GDBlock(object): 
	''' 
	This is the base class of all gicdat extension blocks. It exists solely
	to allow type checking with "isinstance" and "issubclass", and provides no
	API.  All the other template classes in this module subclass it.
	User-written blocks should subclass one of those more detailed templates

	'''
	def __init__(self):
		object.__init__(self)


class Parser(GDBlock):
	''' 
	This is the template for blocks that provide support for file IO

	The work is done by the methods "read" and "write". Subclasses may not
	change the signture of these methods

	canread and canwrite are lists of filetype identifiers that the parsers can
	handle. Extensions is a dictionary mapping file extensions the parsers
	knows about (without the leading ".") to filetype identifiers.

	For a working example, see gicdat.stdblocks.gicparse.JSONParse

	'''
	
	canread = ()
	canwrite = ()
	extensions = {}
	
	def read(self, stream, filetype, **kw):
		'''
		stream is a file like object, open in read mode. filetype is a
		mime-type-like string. kw args are implementation specific
		
		read should return a 2-tuple (d, code). d should be a gicdat.doc.Doc
		instance.
		
		code may be None, or it may be a ZipFile instance that contains
		additional gicdat blocks (which will be passed to
		gicdat.blocks.register)	 
		
		Note that Parsers should _not_ try to handle externalDocuments
		themselves. Just return the include the nodes describing them in d

		'''
		pass

	def write(self, d, stream, filetype, **kw):
		'''
		d is a gicdat.doc.Doc
		
		Stream is a file-like object open in write mode.
		
		filetype is a mime-type-like string. 
		
		kw args are implementation specific

		Write should return None. 

		Write should not concern itself in any way with externalDocuments

		'''
		
		pass

class Transport(GDBlock):
	''' 
	This is the template for blocks that provide the ability to open url
	schemes in order to provide file like objects.

	canread and canwrite are lists of "scheme" strings that the transport can
	handle

	The API of a transport is that it must provide a method "open" which 
	'''
	canread = ()
	canwrite = ()	

	def open(self, url, mode, filetype):
		'''
		Return a file-like object open in mode
		
		'''
		pass

class Tag(GDBlock):
	'''
	The implementation and documentation of the Tag class is actually in the
	module gicdat.tags. This abstract superclass is used only used by
	gicdat.blocks to identify Tags (blocks can't import gicdat.tags directly
	without risking import loops)
	
	''' 
	def __init__(self, pat, info):
		self.__doc__ = info
		self.pat = search.pattern(pat)

def strtoslice(s):
	sl = []
	for sub in s.split(','):
		sub = sub.split(':')
		for i in range(3):
			if len(sub)<i+1:
				sub.append(None)
			elif sub[i]:
				sub[i] = int(sub[i])
			else:
				sub[i] = None
		sl.append(tuple(sub))
	if len(sl)==1:
		return sl[0]
	else:
		return tuple(sl)

class Transform(GDBlock):
	#FIXME
	'''
	Transforms do most of the work of data analysis. The job of a Transform is
	to provide a __call__ method that takes two gicdat.doc.Doc instances,
	and returns a tuple (Doc, list of strings)  (the list may be empty).

	The first input doc contains the data used by the transform. The first
	return value is a "patch" which represents changes to this document as the
	result of running the transform (although in some cases this may be
	interpreted as . The second doc provides the parameters used by the
	transform. It transforms also accept the second argument to be a string, in
	which case it is considered to be a path within the first document where
	the parameters are stored.   
	
	The list of strings is a collection of "reports" that were generated during
	the call method. Transforms should never use "print" or write data to
	files, and they are not responsible for using the gicdat.control interface
	either. If code within the transform fails, it should raise an exception as
	normal, but if it would simply like to tell the user something (for
	debugging, as a warning, to report on the probable validity of a
	computation, etc), then it should add this report to the reports list which
	will be returned by __call__.

	Transforms should specify the attributes "inputs", "outputs", and "defaults",
	which should be dictionaries. "defaults" is used as a starting set of 
	parameters, which is updated by the passed-in parameters during a call. 
	Ideally, a transform should have defaults provided for every parameter, so
	that it is possible to run a test case with no input parameters (even if 
	this case is not typically useful, although if possible it should also be 
	the most useful and common case).
	
	"inputs" and "outputs" are dictionaries that can be passed to 
	gicdat.search.pattern. The resulting pattern specifies the types of the 
	transform's inputs and outputs.  These should be detailed enough that an
	instance can determine if it is possible (and sensible) to run the 
	transform on a given input document and parameter set, by matching self.input
	against self.pars(doc, pars, True). Any output that would be generated 
	by the transform should match self.output (consequently, the system can 
	determine if the output of one transform can be used as input to a second
	transform by calling search.contains(p1.output, p2.input).
	
	Transforms should avoid significant polymorphisms, which make the "input" 
	and "output" patterns inacurate or very complicated. Instead, provide several 
	related transforms.
	
	The base class provides a __call__ which constructs a parameter dictionary 
	including the defaults and passes it to self.run, so subclasses may prefer
	to overload self.run rather than self.__call__
	
	'''
	
	inputs = None
	outputs = None
	defaults = {}
	def __init__(self):
		if self.inputs:
			self.inputs = search.pattern(self.inputs)
		if self.inputs:
			self.outputs = search.pattern(self.outputs)
			
	
	def expandlinks(self, d):
		'''
		returns a patch document for the parameter document d which expands three
		syntactic shortcuts that may be used in writing transform parameters. These
		are key values that are strings beginning with "->". The remainder of such a
		string will be treated as the  _link attribute for a link dictionary. If the
		string ends with a [...]  python slice, this will be parsed and entered as the
		_slice element. If the string begins with "->::" the remainder will be treated
		as a local link within the parameter document (which may be needed when
		building the intermediate steps of a remote or multiprocess tool chain, which
		may recieve input data within the parameter set, rather than in an input
		document)
		
		'''
		patch = d.new()
		lls = []
		for k in d:
			if type(d[k]) in [str, unicode]:
				if d[k].startswith('->::'):
					lls.append((k,d[k][4:]))
				elif d[k].startswith('->'):
					ld = d.new()
					s = d[k][2:]
					if "[" in s:
						s, ss = s.rstrip(']').split('[')
						ld['_slice'] = strtoslice(ss)
					ld['_link'] = s
					patch[k] = ld
		for k,v in lls:
			if v in patch:
				patch[k] = patch[v]
			else:
				patch[k] = d[v]
		return patch
			
	def __call__(self, doc, pars=None):
		'''
		Construct parameters dictionary using defaults if needed, and pass it 
		to self.run
		
		'''
		pars = self.pars(doc, pars, True)
		r = doc.__class__()
		m = []
		self.run(pars, r, m)
		return (r, m)
	
	def extract(self, doc, pars):
		p = pars.new()
		for k in pars.keys(-1):
			if isinstance(pars[k], dict) and pars[k]["_link"]!=None:
				p[k] = doc.resolvelink(pars[k])
				if isinstance(p[k], dict):
					p[k] = p[k].copy()
					p[k+"._link"] = None
					p[k+"._slice"] = None
		return p
	
	def requires(self, doc, pars):
		need = []
		pars = self.pars(doc, pars, extract = False)
		for k in pars.keys(-1):
			if isinstance(pars[k], dict) and pars[k]["_link"]!=None:
				need.append(pars[k]['_link'])
		return set(need)

	def pars(self, doc, pars, extract=True):
		if type(pars) in [str, unicode]:
			pars = doc.sub(pars)
		elif type(pars) == dict:
			pars = doc.__class__(pars)
		elif pars == None:
			pars = doc.__class__()
		if self.defaults:
			pars = doc.__class__(self.defaults).fuse(pars)
		el = self.expandlinks(pars)
		if el:
			pars = pars.fuse(el)
		if extract:
			nd = self.extract(doc, pars)
			if nd:
				pars = pars.fuse(pars, nd)
				pars.clean()
		return pars

	def test(self, doc, pars):
		'''
		Test if the given doc and pars are valid inputs according to
		self.sig (and given self.defaults). If the test succeeds, return 0.
		Otherwise, return a string containing an explanation of the failure.
		
		The test uses search.setContext(self.sig, {'doc':doc}); self.sig ==
		params. The failure return value uses search.whyFailed(self.sig)
		
		'''
		#FIXME
		if self.input == None:
			return "No Signature"
		pars = self.pars(doc, pars, True)
		if self.input == pars:
			return 0
		else:
			return search.whynot(pars, self.pars)
		
	def follows(self, tf):
		'''
		test if this transform can come in a sequence after transform tf 
		'''	
		if not tf.output or not self.input:
			return "Missing Signature"
		if search.contains(tf.output, self.input):
			return 0
		else:
			return search.whynotcontains(tf.output, self.input)
	
	def callWith(self, f, sp, p):
		arg = {}
		for a in inspect.getargspec(f)[0]:
			if a in sp:
				arg[a] = sp[a]
			elif a in p:
				arg[a] = p[a]
		return f(**arg)	
	
	def run(self, pars, out, messages):
		'''
		Do the work, and return a list of strings. Subclasses should overload this.
		'''
		messages.append('called an empty Transform')

class Service(GDBlock):
	pass

