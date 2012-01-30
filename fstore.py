#!/usr/bin/env python -3
# encoding: utf-8

#Created by Graham Cummins on Jul 3, 2011

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

from __future__ import print_function

import os, time, signal, struct

global DIR, DOC, PEND, ACT, PREREQ, NOTIFY, JLOCK, WLOCK, WORK

if os.environ.get("GICDAT_FSTORE_DIR"):
	DIR = os.environ["GICDAT_FSTORE_DIR"]
else:
	DIR = os.path.join(os.environ['HOME'],  '.gicdat', 'fstore')
WORK = os.path.join(DIR, 'workers')
DOC = os.path.join(DIR, 'doc')

INT_S = struct.calcsize("<I")

def build(bd=None):
	global DIR, DOC, PEND, ACT, PREREQ, NOTIFY, JLOCK, WLOCK, WORK
	if bd:
		DIR = bd
		DOC = os.path.join(DIR, 'doc')
		PEND = os.path.join(DIR, 'pending')
		ACT = os.path.join(DIR, 'active')
		PREREQ = os.path.join(DIR, 'prereq')
		NOTIFY = os.path.join(DIR, 'notify')
		JLOCK = os.path.join(DIR, 'jlock')
		WLOCK = os.path.join(DIR, 'wlock')
		WORK = os.path.join(DIR, 'workers')
	for d in [DIR, DOC, PEND, PREREQ, NOTIFY, ACT, WORK]:
		if not os.path.exists(d):
			os.mkdir(d)

def rebuild():
	global DOC, PEND, ACT, PREREQ, NOTIFY, JLOCK, WLOCK, WORK
	if workerpids():
		closeworkers()
		time.sleep(1)
	build()
	for fn in [JLOCK, WLOCK]:
		if os.path.exists(fn):
			os.unlink(fn)
	for d in [DOC, PEND, PREREQ, NOTIFY, ACT, WORK]:
		for fn in os.listdir(d):
			if not fn.startswith('.'):
				os.unlink(os.path.join(d, fn))


try:
	build(DIR)
except:
	#we hope this is a web server without a home directory, and it will set 
	#DIR manually. Can't warn, since mod_wsgi supresses both imports and 
	#use of stdout
	pass

def clearcont():
	signal.signal(signal.SIGCONT, signal.SIG_IGN)

def cont(signum=None, frame=None):
	#print('got signal')
	raise StandardError("Wake up you lazy dog")
	
def wait():
	#print('waiting', os.getpid())
	signal.signal(signal.SIGCONT, cont)
	try:
		while True:
			time.sleep(1)
		#should work, but seems buggy. Ignores signals pretty often
		#_ = signal.pause()
	except KeyboardInterrupt:
		raise
	except StandardError:
		pass
	clearcont()
	signal.signal(signal.SIGCONT, signal.SIG_IGN)
	#print('woke up', os.getpid())
	
def workerpids():
	pids = []
	for fn in os.listdir(WORK):
		try:
			pids.append(int(fn))
		except ValueError:
			pass
	return pids

def sigworkers(sig):
	for pid in workerpids():
		try:
			os.kill(pid, sig)
		except OSError:
			fn = os.path.join(WORK, str(pid))
			if os.path.exists(fn):
				os.unlink(fn)

def wakeworkers():
	sigworkers(signal.SIGCONT)
		
def closeworkers(overkill=True):
	if overkill:
		for fn in os.listdir(WORK):
			try:
				pid = int(fn)
			except ValueError:
				continue
			os.kill(pid, signal.SIGKILL)
			try:
				os.unlink(os.path.join(WORK, fn))
			except:
				pass
	else:	
		sigworkers(signal.SIGTERM)
	
	

def acquire(lfile=JLOCK):
	fid = None
	while fid==None:
		try:
			fid = os.open(lfile, os.O_RDWR | os.O_CREAT | os.O_EXCL)
		except:
			time.sleep(1)
	os.write(fid, str(os.getpid()))
	os.close(fid)
	return fid

def release(lfile=JLOCK):
	os.unlink(lfile)

def allids(dirs = (DOC, PEND, ACT, PREREQ)):
	ids = []
	for d in dirs:
		for fn in os.listdir(d):
			try:
				ids.append(int(fn))
			except:
				pass
	return ids

def readpr(fn):
	try:
		f = open(fn, 'r')
		npr = struct.unpack("<I", f.read(INT_S))[0]
		pr = struct.unpack("<"+"I"*npr, f.read(INT_S*npr))
		f.close()
		return pr
	except OSError:
		time.sleep(1)
		return readpr(fn)

def readpl(fn):
	try:
		f = open(fn, 'r')
		npr = struct.unpack("<I", f.read(INT_S))[0]
		f.seek(INT_S*(npr+1))
		s = f.read()
		f.close()
		return s
	except OSError:
		time.sleep(1)
		return readpl(fn)
	
def writewithpr(fn, s='', pr=None):
	try:
		if not pr:
			pr = []
		f = open(fn, 'w')
		f.write(struct.pack("<I", len(pr)))
		f.write(apply( struct.pack, ["<" + "I"*len(pr)]+list(pr) ) )
		f.write(s)
		f.close()
	except OSError:
		time.sleep(1)
		return writewithpr(fn, s, pr)

def completed(id, dir=PREREQ):
	c = []
	for fn in os.listdir(dir):
		ids = readpr(os.path.join(dir, fn))
		if ids and id in ids:
			if set(ids).issubset(allids([DOC]) + [id]):
				c.append(fn)
	return c

def updateprereqs(id):
	pr = completed(id, PREREQ)
	for fn in pr:
		os.rename(os.path.join(PREREQ, fn), os.path.join(PEND, fn))

def nextid():
	i = 0
	v = allids()
	while i in v:
		i = i+1
	return i
		
def adddoc(doc):
	id = nextid()
	fn = os.path.join(DOC, str(id))
	open(fn, 'w').write(doc)
	return id

def deldocs(ids):
	for id in ids:
		os.unlink(os.path.join(DOC, str(id)))


def getdoc(id, block=True):
	if id in allids([DOC]):
		return open(os.path.join(DOC, str(id))).read()
	elif block:
		return collect([id])['j0']
	else:
		return None

def getdocs(ids, pref='j', block=True):
	nd = {}
	for i, id in enumerate(ids):
		nd['%s%i' %(pref, i+1)] = getdoc(id, block)
	return nd
		
def finish(doc, id):
	acquire(WLOCK)
	try:
		updateprereqs(id)
		nff = completed(id, NOTIFY)
		fn = os.path.join(DOC, str(id))
		open(fn, 'w').write(doc)
		os.unlink(os.path.join(ACT, str(id)))
	finally:
		release(WLOCK)
	for fn in nff:
		os.kill(int(fn), signal.SIGCONT)
		os.unlink(os.path.join(NOTIFY, fn))
	return id
	
def addnotify(docids, pid=None):
	if not pid:
		pid = os.getpid()
	fn = os.path.join(NOTIFY, str(pid))
	writewithpr(fn, '', docids)
	return pid

def collect(docids, delete=(), pref='j'):
	acquire(WLOCK)
	try:
		if set(docids).issubset(allids([DOC])):
			done = True
		else:
			done = False
			addnotify(docids)
	finally:
		release(WLOCK)
	if not done:
		wait()
	d = getdocs(docids, pref, False)
	deldocs(delete)
	return d

def addjobs(jobs, prereqs):
	if not prereqs:
		prereqs = [[]]*len(jobs)
	ids = []
	acquire(WLOCK)
	try:
		alldocs = allids([DOC])
		for i in range(len(jobs)):
			id = nextid()
			fn = str(id)
			if set(prereqs[i]).issubset(alldocs):
				fn = os.path.join(PEND, str(id))
			else:
				fn = os.path.join(PREREQ, fn)
			writewithpr(fn, jobs[i], prereqs[i])
			ids.append(id)
	finally:
		release(WLOCK)
	wakeworkers()
	return ids	

def alljobs():
	jobs = []
	for fn in os.listdir(PEND):
		try:
			fid= int(fn)
			jobs.append(fid)
		except:
			pass
	return sorted(jobs)
	

def getjob():
	acquire(JLOCK)
	try:
		jobs = alljobs()
		if jobs:
			jid = jobs[0]
			ffn = os.path.join(PEND, str(jid))
			pre = readpr(ffn)
			open(os.path.join(ACT, str(jid)), 'w').write(str(os.getpid()))
			j = (jid, pre, readpl(ffn))
			os.unlink(ffn)	
		else:
			j = None	
	finally:
		release(JLOCK)
	return j
