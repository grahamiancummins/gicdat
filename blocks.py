#!/usr/bin/env python
# encoding: utf-8
#Created by gic on 2007-04-10.

# Copyright (C) 2007 Graham I Cummins
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

import control, sys, inspect
import base
import stdblocks.__init__

FAILED_LOAD={}
MODS = {}
CONTROLLERS = []
BLOCKS = []
FILES = ['stdblocks']
FILES.extend(control.ENV.get('blocks', []))


#all blocks should be instances. Don't import any instances unqualified

def tryLoad(mn):
	'''
	Load package mn. If it contains __gicdat__ (list of subpackages) load all of these. Otherwise If it includes 
	__all__, load those subpackages. If you write a gicdat madule that contains __all__ in __init__.py, but 
	doesn't use it to point exclusively at sub-packages that should be loaded as blocks (for example because you 
	want to refference individual modules in __all__ so as to support from mypackage import *), then you will 
	need to specify __gicdat__=[], in order to prevent tryLoad from treating these references as additional 
	blocks. 
	'''
	try:
		if mn in MODS:
			control.report('reloading %s' % mn)
			reload(MODS[mn])
		else:
			exec "import %s as mod" % mn
			MODS[mn]=mod
			if mn in FAILED_LOAD:
				reload(mod)
				del(FAILED_LOAD[mn])
		if hasattr(MODS[mn], "__gicdat__"):
			for s in MODS[mn].__gicdat__:
				tryLoad(mn + "." + s)
		elif hasattr(MODS[mn], "__all__"):
			for s in MODS[mn].__all__:
				tryLoad(mn + "." + s)
	except:
		e = sys.exc_info()
		FAILED_LOAD[mn]=e
		if mn in MODS:
			del(MODS[mn])
		control.error(e, None, "error loading module %s" % mn)
	return MODS.get(mn)

def bounce(deep=False):
	if deep:
		for k in MODS.keys():
			del(MODS[k])
		for k in FAILED_LOAD.keys():
			del(FAILED_LOAD[k])
	for mn in FILES:
		tryLoad(mn)
	while BLOCKS:
		BLOCKS.pop()
	for mn in MODS:
		mod = MODS[mn]
		for attr in dir(mod):
			a = getattr(mod, attr)
			if isinstance(a, base.GDBlock):
				a.__name__ = mn + '.' + attr
				BLOCKS.append(a)
				
bounce()


def parsers():
	'''
	Return a list of gicdat.base.Parser instances

	'''
	return [p for p in BLOCKS if isinstance(p, base.Parser)]

def urlschemes():
	'''
	Return a list of gicdat.base.Transport instances
	'''

def tags():
	return dict([(x.__name__, x) for x in BLOCKS if isinstance(x, base.Tag)])


def transforms(names = False):
	td = dict([(x.__name__, x) for x in BLOCKS if isinstance(x, base.Transform)])
	if names:
		return sorted(td.keys())
	else:
		return td

def transform(s):
	for x in BLOCKS:
		if isinstance(x, base.Transform):
			if x.__name__ == s:
				return x
	return None

def shorttf(s):
	'''
	transform match based on the last element of a dot separated name. 
	Returns a list if the match is not unique
	'''
	m = []
	for x in BLOCKS:
		if isinstance(x, base.Transform):
			if x.__name__.split('.')[-1] == s:
				m.append(x)
	if len(m) == 1:
		return m[0]
	else:
		return m
	

def register(code):
	'''
	Register additional extension modules. Code may be a list of Python module names, a list of absolute path names, or a zipfile.

	'''
	control.report('oops, blocks.register isnt finished yet')
	#FIXME

class BlockAccess(object):
	def transforms(self, names = False):
		return transforms(names)
	def transform(self, s):
		return transform(s)
	def parsers(self):
		return parsers()
	def tags(self):
		return tags()
			
control.blocks = BlockAccess()