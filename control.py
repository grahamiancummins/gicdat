#!/usr/bin/env python -3
# encoding: utf-8

#Created by gic on Sun Oct 24 14:33:52 CDT 2010

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

import time, StringIO, traceback, os, sys
import getpass

'''
This module provides an anchor point for gicdat controls to register
themselves. Other gicdat modules use methods report, error, and update to
notify associated controllers of changes.	

'''


CONTROLLERS = []
ENV = {'gui':False
	  	
	  }


if os.environ.get('GICDAT_CONF'):
	CONF_DIR = os.environ['GICDAT_CONF']
else:
	CONF_DIR = os.path.join(os.environ['HOME'], ".gicdat")
if not os.path.isdir(CONF_DIR):
	os.mkdir(CONF_DIR)
if not os.path.isfile(os.path.join(CONF_DIR, 'env.py')):
	open(os.path.join(CONF_DIR, 'env.py'), 'w').write("{}")
ENV.update(eval(open(os.path.join(CONF_DIR, 'env.py')).read()))

for path in ENV.get('path_prepend', []):
	sys.path.insert(0, path)

for path in ENV.get('path', []):
	sys.path.path(path)




class GicdatError(StandardError):
	'''Trivial exception subclass raised by Doc and Node "error" methods'''
	pass

def asksecret(prompt="Password :"):
	return getpass.getpass(prompt)
	
def report(s, t=None):
	if not type(s) in [str, unicode]:
		s = str(s)
	if not t:
		t = time.time()
	for c in CONTROLLERS:
		c.report(s, t)
	if not CONTROLLERS:
		if ENV.get('log'):
			open(ENV['log'], 'a').write(s)
		else:
			print(s)

def error(e, t=None, rep=False):
	if not t:
		t = time.time()
	if rep:
		s = StringIO.StringIO()
		s.write(rep + "\n")
		traceback.print_exception(e[0], e[1], e[2], file = s)
		report(s.getvalue())
		s.close()
	else:
		for c in CONTROLLERS:
			c.error(e, t)
		raise e

def update(doc):
	for c in CONTROLLERS:
		c.update(doc)

blocks = None

