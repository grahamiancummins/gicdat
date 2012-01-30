#!/usr/bin/env python -3
# encoding: utf-8


# Created by Graham Cummins on 
# Mon Feb 28 12:45:45 CST 2011
#
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
import numpy as np
import matplotlib.pyplot as plt

class CircleList(list):
	def __getitem__(self, i):
		return list.__getitem__(self, i%len(self))

COLORS = CircleList(['b', 'r', 'g', 'k'])
LSTYLES = CircleList(['-', '--', '-.', ':', '.', 'o', 'v', '^'])

def gplot(groups, glen='auto'):
	''' 
	Groups is a tuple of tuples of
	tuples of ints, which specifies groups of sets of spike trains. 

	'''
	if glen == 'auto':
		glen = max([len(g) for g in groups])
	for i, g in enumerate(groups):
		col = COLORS[i]
		if i%2:
			plt.axhspan(glen*i, glen*(i+1)-1, facecolor=(.8,.8,1), alpha=0.3, edgecolor='none')
		for eti, et in enumerate(g):
			ylev =  i*glen + eti
			y = np.ones(len(et)) + ylev		
			plt.plot(et, y, marker='.',color=col, linestyle='None')
	return ylev

def grect(n):
	#y = 9/16 x
	#x * y = n
	#9x**2/16 = n
	#x**2 = 16n/9
	x = np.sqrt( (16.0*n)/9.0)
	y = int( round((9.0*x)/16.0))
	x = int(round((x)))
	while x*y < n:
		x=x+1
		if x*y <n:
			y = y+1
	return (y, x)

def hists(a):
	f = plt.figure(1)
	plt.clf()
	ht = 0
	for i in range(a.shape[0]):
		d = a[i,:]
		x = np.nonzero(d)[0]
		plt.bar(x, d[x],.8, ht)
		ht+=d.max()+1
	plt.xlim([0, a.shape[1]])
	plt.ylim([0, ht])
	f.canvas.draw()

