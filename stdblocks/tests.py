#!/usr/bin/env python -3
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

from __future__ import print_function, unicode_literals

from gicdat.base import Transform
import gicdat.search as gds

nullsig = gds.pattern({})

class Identity(Transform):
	sig = nullsig
	
	def run(self, pars, out, messages):
		for k in pars.keys(-1, subdockeys=False):
			out[k] = pars[k]



class AddTo(Transform):
	defaults = {'x':1.0}
	sig = gds.pattern({'x':'ixz', 'addto':'ixz'})
	
	def run(self, pars, out, messages):
		out['n'] = pars['x'] + pars['addto']
		messages.append('ran addto')

id = Identity()
add = AddTo()