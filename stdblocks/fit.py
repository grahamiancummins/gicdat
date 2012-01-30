#!/usr/bin/env python
# encoding: utf-8
#Created by gic on 2007-04-10.

# Copyright (C) 2007 Graham I Cummins This program is free software; you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc., 59
# Temple Place, Suite 330, Boston, MA 02111-1307 USA

from __future__ import print_function, unicode_literals

from gicdat.base import Transform


def _ediff(v, x, y, s):
	"""Internal, used by the least squares call in expfit"""
	e =y -  v[0]*np.exp(-1*v[1]*x) 
	if s!=None:
		e = e/s
	return e

def expfit(x, y, s):
	'''
	x:N-[ of x, y:N-[ of x, s:N-[ of x -> (A of x, l of x)
	
	Estimate the best exponential fit to data samples x, y, with scale factor s
	
	This is the fit that minimizes the sum of squares of:
	( y - A*exp(-1*l*x) )/s
	
	Used by showscan, if it is asked to show an exponential fit to data.
	
	Currently, s is not used (any false value of s is equivalent to passing an
	array of ones, but faster). In principal, passing a monotonic function
	can be used to make the fit more or less sensitive to the early decay
	compared to the asymptotic value
	
	no longer used in this module, but was called as:
	
	exv = np.linspace(xvals.min(), xvals.max(), 40)
	efit = expfit(xvals, mi, None ) 
	plt.plot(exv, efit[0]*np.exp(-1*efit[1]*exv), 
		color=styles[sid][0], linestyle='--', 
		label="Fit to %s, $\lambda = $ %.3g" % (k,efit[1]))

	
	
	'''
	a = np.argmax(x)
	xu = x[a]
	yu = y[a]
	a = np.argmin(x)
	xd = x[a]
	yd= y[a]
	if xd == 0:
		A = yd
		l = - np.log(yu)/xu
	else:
		#yu/yd = exp(-1*l*(xu-xd)) from scale invariance
		l = - np.log(yu/yd)/(xu-xd)
		A = yd/np.exp(-l*xd)
	fp=opt.leastsq(_ediff, np.array([A, l]), (x, y, s), maxfev = 4000)
	return tuple(fp[0])