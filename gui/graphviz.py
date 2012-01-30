#!/usr/bin/env python -3
# encoding: utf-8

#Created by Graham Cummins on 

# Copyright (C) 2011 Graham I Cummins
# This program is free software; you can redistribute it and/or modify it
#underthe terms of the GNU General Public License as published by the Free
#Software Foundation; either version 2 of the License, or (at your option) 
#any later version.

#This program is distributed in the hope that it will be useful, but WITHOUT 
#ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS 
#FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

#You should have received a copy of the GNU General Public License along with
#this program; if not, write to the Free Software Foundation, Inc., 59 Temple
#Place, Suite 330, Boston, MA 02111-1307 USA

import gicdat.doc as gd
import os, re

def displaydot(dot, fn='gic_viz'):
	if not fn.endswith('dot'):
		fn=os.path.splitext(fn)[0]+'.dot'
	open(fn,'w').write(dot)
	os.system("dot -Tpng -O %s" % fn)
	os.system("display %s.png" % fn)
	return dot	

def lgraph(layers, connections, fn=''):
	dot=["digraph G {",
		'graph [center=1, rankdir="LR"];']
	cgraph=["subgraph connections {"]	
	sgl=0
	for i, l in enumerate(layers):
		print i, l
		dot.append("subgraph lev_%i {" % (i,))
		dot.append("rank = same;")
		for j, n in enumerate(l):
			nn = "l%in%i" % (i, j)
			dot.append('%s [label="%s"];' % (nn, n))
		dot.append("}")
	dot.append("subgraph connections {")
	for c in connections:
		n1 = "l%in%i" % (c[0], c[1])
		n2 = "l%in%i" % (c[2], c[3])
		dot.append("%s->%s;" % (n1, n2))		
	dot.append("}")
	dot.append("}")
	dot="\n".join(dot)
	if fn:
		displaydot(dot, fn)
	else:
		return dot


def _dglayer(d, pk):
	dot = []
	for k in d:
		dot.append('%s_%s [label="%s:%s"];' % (pk, k, k, d.summary(k).strip()))
		dot.append('%s -> %s_%s;' % (pk, pk, k))
	for k in d:
		if type(d[k]) == type(d):
			dot.extend(_dglayer(d[k], "%s_%s" % (pk, k)))
	return dot


DIG = re.compile("(.*\D)(\d+)$")
	
def _dglayer_ks(d, pk):
	dot = []
	basekeys = {}
	drill = []
	for k in sorted(d):
		m = DIG.match(k)
		if m:
			bk, n = m.groups()
			n = int(n)
			if bk in basekeys:
				basekeys[bk][0] = min( basekeys[bk][0], n)
				basekeys[bk][1] = max( basekeys[bk][1], n)
				basekeys[bk][2]+=1
				continue
			else:
				basekeys[bk] = [n, n, 0]
		dot.append('%s_%s [label="%s:%s"];' % (pk, k, k, d.summary(k).strip()))
		dot.append('%s -> %s_%s;' % (pk, pk, k))
		if type(d[k]) == type(d):
			drill.append(k)
	for k in sorted(basekeys):
		if basekeys[k][2] == 0:
			continue
		l = "%s (%i - %i: %i keys)" % (k, basekeys[k][0], basekeys[k][1], 
		                               basekeys[k][2])
		dot.append('%s_%s [label="%s"];' % (pk, k, l))
		dot.append('%s -> %s_%s;' % (pk, pk, k))
	for k in drill:
		dot.extend(_dglayer_ks(d[k], "%s_%s" % (pk, k)))
	return dot
	
	
def docgraph(d, fn='doc.dot', show=True, simplify=True, rankdir='LR'):
	#rankdir may be TB or LR
	dot=["digraph G {",
		'graph [center=1, rankdir="%s"];' % rankdir]
	dot.append('root [label="d"];')
	if simplify:
		dot.extend(_dglayer_ks(d, 'root'))
	else:
		dot.extend(_dglayer(d, 'root'))
	dot.append("}")
	dot="\n".join(dot)
	if show:
		displaydot(dot, fn)
	elif fn:
		open(fn,'w').write(dot)
	return dot	