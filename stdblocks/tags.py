#!/usr/bin/env python -3
# encoding: utf-8

#Created by gic on 
#Mon Nov 22 08:34:43 CST 2010

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

from gicdat.base import Tag


timeseries_doc= '''
Tag type for "timeseries" data

To be a timeseries, a node must have tag == 'timeseries', must specify some
numerical value for "samplerate" and "start", and must contain 2D
real-valued data.  These data are organized such that rows are sequential
samples, and columns are different "channels" (different obsereved
variables). Single channels timeseries are fine, but they should be 2D of
shape (N,1) to facilitate consistant handling by processing tools.

Timeseries have the special semantics that they are interpreted as
functions of time (or some other independent variable), such that element
T[i,0] is treated as the x,y point (start+(i/samplerate), T[i,0]). Many
visualization and analysis specify timeseries data as the input type

'''

timeseries_t = Tag({'tag':'=timeseries', 
					'samplerate':'ix',
					'start':'ix',
					'dat':"2,X-# of ix"},
					info=timeseries_doc)
events_doc= '''
Tag type for "events" data

To be events, a node must have tag == 'events', must specify some
numerical value for "samplerate" and "start", and must contain 2D
int-valued data.  These data are organized such that rows are sequential
events. Each event is the integer sample index on which an event occured.

If the data has more than one column, then the second and subsequent 
columns are treated as information about the event listed in the first 
column. Typically, there will be only one additional column, containing the
"identity" of the event (for example the channel it was detected on, the 
signal source that produced it, etc). Further channels, such as the intensity
or subtype of event may also exist.

Events have the special semantics that they are interpreted as
Sequences of discreet events in time (or some other independent variable), 
such that an event value of i occurs at t = start+(i/samplerate). Many
visualization and analysis specify event data as the input type, and 
event data are used to condition timeseries data.

'''					
#events_t = Tag({'tag':'events', 
#					'samplerate':search.REAL,
#					'start':search.REAL,
#					'':search.ArrayOf(
#						search.TupleOf(2, None), 
#						search.INT)
#				},
#				info=events_doc)
