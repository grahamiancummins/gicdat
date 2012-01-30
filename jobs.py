#!/usr/bin/env python
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
from control import report
from util import combine
import blocks, enc
from doc import Doc
import os, time
from traceback import format_exc

def pspace(ranges):
	if not ranges:
		return [{}]
	n = ranges.keys()
	v = [ranges[k] for k in n]
	pars = []
	ps = combine(v)
	for p in ps:
		pars.append(dict(zip(n, p)))
	return pars
	
def prange(transform, baseparams,ranges):
	jobs = []
	baseparams = Doc(baseparams)
	for pd in pspace(ranges):
		jobs.append(Job(transform, baseparams.fuse(pd)))
	return jobs

class Job(object):
	def __init__(self, transform='', params=None, outpath=''):
		self.t = transform
		self._t = None
		self.p = Doc()
		if params:
			self.p.update(params, True)
		self.o = outpath or ''
		
	def __str__(self):
		return "Job: %s\n-----\n%s\n--------\n" % (self.t.__name__, str(self.p))	
		
	def gettf(self):
		if self._t == None:
			self._t = blocks.transform(self.t)
		return self._t
		
		
	def keys(self, doc):
		ks = self.gettf()(doc, self.p)
		if isinstance(self.o, dict):
			for k in self.o:
				if k.startswith('->'):
					ks.add(self.o[k])
		if '' in ks:
			ks = set(doc.keys())
		return ks	
		
	def __call__(self, doc, subset=()):
		try:
			d, m = self.gettf()(doc, self.p)
			for s in m:
				report(s)
			dd = doc.subset(subset)
			if self.o:
				dd[self.o] = d
			else:
				dd = dd.fuse(d)
		except Exception as e:
			dd = Doc({'_failed':True,
	                '_traceback':format_exc(e),
	                '_input':doc,
	                '_job':self.todoc()})
		return dd
	
	def todoc(self, mode='doc'):
		d = Doc()
		d['t'] = self.t
		d['p'] = self.p
		d['o'] = self.o
		if mode=='doc':
			return d
		elif mode == 'tup':
			return d.astuple()
		else:
			return enc.tojson(d)

def dt2j(t):
	d = Doc(t)
	return Job(d['t'], d['p'], d['o'])

from multiprocessing import Pool

POOL_IDOC = None
POOL_J = None

def poolworker(arg):
	j = dt2j(POOL_J)
	d = Doc(POOL_IDOC)
	return j(d[arg])

def jobpool(t, p, d, k, n):
	global POOL_IDOC
	global POOL_J
	POOL_J = Job(t, p).todoc('tup')
	POOL_IDOC = d.astuple()
	keys = d.keys(0, k)
	p = Pool(n)
	r = p.map(poolworker, keys)
	p.close()
	nd = Doc()
	for i, k in enumerate(keys):
		nd[k] = r[i]
	return nd
	


SEQNOTES="""

There used to be an extensive function called "sequence" here, which made
many types of job sequences. Most of these are better constructed by hand.

Just remember that a job sequence is:
(N-[ of Job, p of N-[ of [ of i, r of [ of i)

where:

p, the prequisites list, contains at index i a list of integers representing 
documents that are needed in order to evaluate the job at index i. In this list,
the value -1 refers to the original input document, and any non-negative integer
j refers to the result of running the job at index j. The input document is the
result of running a "fuse" on the list of documents in the order they occur in
p[i]. An empty sequence is legal input, and implies that not even an initial
document is needed. This is possibly appropriate for jobs that synthesize output
(such as a parametric function generator or random source).

r, the return list, is a list of indexes of jobs who's results you want
returned. 

For examples:
Assume an N-[ of jobs js,

a job pool (a bunch of unrelated jobs that run in parallel) looks like:
(js, [[-1]]*len(js), range(len(js)))

a tool chain (do each thing in linear order, and return the last thing),
looks like:

(js, [[i-1] for i in range(len(js))], [len(js)-1] )

The function prlists(l) can be convenient for constructing the prerequisit
list when each prereq is single. It simply converts all integers i to lists
[i] within l, and doesn't change elements that are already lists.

"""

def prlists(l):
	pr = []
	for p in l:
		if type(p) == int:
			pr.append([p])
		else:
			pr.append(p)
	return pr

def toolchain(js):
	return (js, [[i-1] for i in range(len(js))], [len(js)-1] )

def flatscan(trans, par, ran):
	jobs = prange(trans, par, ran)
	ret = range(len(jobs))
	return (jobs, [-1]*len(jobs), ret)

def pr_seq(jid, prs):
	hist = []
	pr = prs[jid][-1]
	while pr!=-1:
		hist.append(pr)
		pr = prs[pr][-1]
	hist.reverse()
	return hist

def pr_seq_full(jid, prs):
	hist = [jid]
	for pr in prs[jid]:
		if pr>=0:
			hist.extend(pr_seq_full(pr, prs))
	return hist
	
def tieredscan(trans, par, ran, out=None, forward = None, reentry=None):
	pt = [-1]
	prs = []
	jobs = []
	par = [Doc(p) for p in par] 
	out = out or {}
	forward = forward or {}
	reentry = reentry or {}
	for tier in range(len(trans)):
		npt = []
		parset = pspace(ran[tier])
		for ptid in pt:
			for pars in parset:
				jid = len(jobs)
				prs.append([ptid])
				for rei, re in enumerate(reentry.get(tier) or []):
					if re==-1:
						prs[-1].insert(rei, -1)
					else:
						prs[-1].insert(rei,pr_seq(jid, prs)[re])
				pars = par[tier].fuse(pars)
				if forward.get(tier):
					prseq = pr_seq(jid, prs)
					for fk in forward[tier]:
						fkv = forward[tier][fk]
						ss = jobs[prseq[fkv[0]]].p[fkv[1]]
						if callable(fkv[2]):
							ss = fkv[2](ss)
						else:
							ss = ss + fkv[2]
						pars[fk] = ss
				op = out.get(tier) or ''
				if op.startswith('->'):
					op = pars[op[2:]][2:]
				jobs.append(Job(trans[tier], pars, op))
				npt.append(jid)
		pt = npt
	return (jobs, prs, npt)

def job_seq(jid, seq):
	ids = pr_seq_full(jid, seq[1])
	pd = Doc()
	for j in ids:
		pd['j%i' % j] = seq[0][j].todoc()
	return pd

def param_composit(jid, seq):
	ids = pr_seq_full(jid, seq[1])
	ids.reverse()
	return Doc.fuse(*[seq[0][i].p for i in ids])

def annotate_seq(r, seq, full=True):
	for i, j in enumerate(seq[2]):
		if full:
			p = job_seq(j, seq)
		else:
			p = param_composit(j, seq)
		r['j%i' % (i+1,)]['_params'] = p 
	
def subset(doc, jobs, prereqs=None):
	if prereqs:
		jobs = [jobs[i] for i in range(len(jobs)) if -1 in prereqs[i]]
	keys = [j.keys(doc) for j in jobs]
	keys = reduce(keys[0].union, keys)
	return doc.subset(keys)

def do_sequence(seq, doc):
	jobs, pr, ret = seq
	ops = {-1:doc}
	for jid in range(len(jobs)):
		inp = Doc().fuse(*[ops[i] for i in pr[jid]])
		ops[jid] = jobs[jid](inp)
	out = Doc()
	for i,n in enumerate(ret):
		out['j%i' % (i+1,)] = ops[n]
	return out 

def d2str(d):
	return enc.tozip(d)

def str2d(s):
	return enc.fromzip(s)

CTYPE = 'application/zip'

def distribute_sequence(seq, doc):
	import fstore
	js, prs, ret = seq
	if not prs:
		prs = [[-1]] * len(js)
	#doc = subset(doc, js, prs)
	did = fstore.adddoc(d2str(doc))
	jids = []
	for i, j in enumerate(js):
		pr = [jids[x] for x in prs[i] if x>=0]
		if -1 in prs[i]:
			pr = [did]+pr
		jids.extend(fstore.addjobs([d2str(j.todoc())], [pr]))
	if ret!=None:
		ret = [jids[r] for r in ret]
	else:
		ret = jids
	r = fstore.collect(ret, [did]+jids, 'j')
	nd = Doc()
	for k in r:
		nd[k] = str2d(r[k])
	return nd
	
def workloop(rep):
	print('starting worker')
	import fstore
	pid = str(os.getpid())
	fstore.clearcont()
	pidfile = os.path.join(fstore.WORK, pid)
	open(pidfile, 'w').write(pid)
	try:
		while True:
			rep('entering loop')
			j = fstore.getjob()
			if not j:
				fstore.wait()
				rep('woke up')
				continue
			rep('decoding')
			jid, inps, j=j
			j = str2d(j)
			rep('have job %s' % jid)
			d = Doc()
			for did in inps:
				d.patch(str2d(fstore.getdoc(did)))
			if "_failed" in d:
				r = d
			else:
				j = Job(j['t'], j['p'], j['o'])
				r = j(d)
			rep('finishing %s' % j.t)
			r = d2str(r)
			fstore.finish(r, jid)
			rep('done')
	except SystemExit, KeyboardInterrupt:
		print('exiting worker')
		os.unlink(pidfile)

def startworkers(n=None, bg=True, debug=False):
	if debug:
		def rep(s):
			print(s)
	else:
		def rep(s):
			pass
	if not n:
		from multiprocessing import cpu_count
		n = cpu_count()
	if not bg:
		n = n-1
	master = True
	if n:
		for _ in range(n):
			if master:
				pid = os.fork()
				if not pid:
					master = False
	if not master:
		workloop(rep)
	elif not bg:
		workloop(rep)


