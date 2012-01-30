#!/usr/bin/env python -3
# encoding: utf-8

#Created by gic on 2010-12-13

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
import sys, os, getopt
from gicdat.control import report
bogousage ='''
This message was probably reported in gicdat.cli because a command was called
with the wrong options or arguments. Unfortunately, the particular command didn't 
include any informative usage information, so you are pretty much SOL.
'''

def swparse(shortopts='', usage=bogousage, longopts= ()):
	'''
	Parse command line arguments using getopt.gnu_getopt, but at a slightly 
	higher level. shortopts and longopts are the string and list arguments 
	to getopt (defaulting to '' and () respectively). Usage is a documentation 
	string. If parsing fails, or if the option "-h" is passed, usage is printed 
	and SysExit is raised. Otherwise, the return value is (options 
	<{str:str}>, files <[str]>), The dictionary options has keys containing 
	any command line options, with the leading dashes stripped off, associated 
	to their values (if any). Files is a list of the remaining command line 
	arguments.
	'''
	try:
		options, files = getopt.gnu_getopt(sys.argv[1:], shortopts, longopts)
	except getopt.error:
		report(usage)
		sys.exit()	
	switches={}
	for o in options:
		switches[o[0].lstrip('-')]=o[1]
	if 'h' in switches:
		report(usage)
		sys.exit()
	return switches, files	

def dispatch( copts, ddict, key=''):
	'''
	Dispatch functions based on command line options. Copts is <({str:str}, [str])> as
	returned by swparse. ddict is <{str:function}> containing a list of possible functions
	to dispatch. Each of these will, if selected, be called as apply(f, copts), so each 
	should expect two receive two arguments, opts, files (see swparse for details). 
	
	The function is selected in one of two ways. If "key" is the empty string (which is the 
	default), then for every key in copts[0], if that key exists in ddict, the associated 
	function is called (note that the search order is not well specified, so don't use this
	method if there might be multiple matches). If "key" is not empty, then it should 
	exist in copts, have a value, the value should exist in ddict, and its associated 
	function is called (failure of these conditions throws a KeyError). 
	
	The return value of dispatch is the return value of the dispatched function
	'''
	if not key:
		for k in copts[0]:
			if k in ddict:
				return ddict[k](copts)
		raise KeyError('No known function was specified for dispatch')
	else:
		return ddict[copts[0][key]](copts)

clusage = '''
This command uses the usage pattern:
	command subcommand [opts] [args]

The following are a list of supported subcommands:

help - print this message

SCMD

For the usage of particular subcommands, use:
command help subcommand

The full list of supported command line options is:
CLO
The meaning of these options (including whether they are allowed or required)
will depend on the subcommand that is called

'''

def cldispatch(functs, shortopts='', longopts=[]):
	'''
	This function supports "command dispatch", for producing a command that
	takes, as its first argument, a subcommand (for example, git works in this
	way). 
	
	functs may be either a list of functions, or a dictionary of
	{str:function}.  In the former case, the list is converted to a dict using
	f.__name__ as the key for f. 

	'''
	if type(functs)!=dict:
		functs = dict([(f.__name__, f) for f in functs])
	usage = clusage.replace("SCMD", "\n".join(functs))
	usage =  usage.replace("CLO", shortopts+" " + " ".join(longopts))
	try:
		opts, args = swparse(shortopts, usage, longopts)
		cmd = args[0]
		if cmd.lower() == "help":
			f = functs[args[1]]
			report(f.__doc__)
			sys.exit()
		else:
			f = functs[cmd]
	except SystemExit:
		raise
	except:
		print(sys.exc_info())
		report(usage)
		sys.exit()
	args = args[1:]
	return f(opts, args)
		
		
	








