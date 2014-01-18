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

from gicdat.doc import Doc
import enc


def pr_seq_full(jid, prs):
    hist = [jid]
    for pr in prs[jid]:
        if pr >= 0:
            hist.extend(pr_seq_full(pr, prs))
    return hist


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
        r['j%i' % (i + 1,)]['_params'] = p


def subset(doc, jobs, prereqs=None):
    if prereqs:
        jobs = [jobs[i] for i in range(len(jobs)) if -1 in prereqs[i]]
    keys = [j.keys(doc) for j in jobs]
    keys = reduce(keys[0].union, keys)
    return doc.subset(keys)


def do_sequence(seq, doc):
    jobs, pr, ret = seq
    ops = {-1: doc}
    for jid in range(len(jobs)):
        inp = Doc().fuse(*[ops[i] for i in pr[jid]])
        ops[jid] = jobs[jid](inp)
    out = Doc()
    for i, n in enumerate(ret):
        out['j%i' % (i + 1,)] = ops[n]
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
        pr = [jids[x] for x in prs[i] if x >= 0]
        if -1 in prs[i]:
            pr = [did] + pr
        jids.extend(fstore.addjobs([d2str(j.todoc())], [pr]))
    if ret != None:
        ret = [jids[r] for r in ret]
    else:
        ret = jids
    r = fstore.collect(ret, [did] + jids, 'j')
    nd = Doc()
    for k in r:
        nd[k] = str2d(r[k])
    return nd