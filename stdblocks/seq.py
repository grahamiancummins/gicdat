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
from gicdat.doc import Doc


class Rename(Transform):
    sig = {}
    defaults = {'doc': '->', 'map': False}

    def run(self, pars, out, messages):
        if pars['map']:
            assigned = []
            d = pars['doc']
            m = pars['map']
            for k in m:
                out[k] = d[m[k]]
                if not m[k] in assigned:
                    out[m[k]] = None
                    assigned.append(m[k])


def seq2doc(seq):
    d = Doc({'pr': seq[1], 'ret': seq[2]})
    for i, j in enumerate(seq[0]):
        d['j%i' % (i + 1,)] = j.todoc()
    return d


class Sequence(Transform):
    sig = {}
    defaults = {'colate': None, 'server': None, 'doc': '->',
                'parallel': None}

    def run(self, pars, out, messages):
        import gicdat.jobs

        js = []
        for jk in pars.keys(0, 'j', sort=True):
            d = pars[jk]
            js.append(gicdat.jobs.Job(d['t'], d['p'], d['o']))
        seq = (js, pars['pr'], pars['ret'])
        doc = pars['doc']
        serv = pars['server']
        if pars['server']:
            import gicdat.eval

            r = gicdat.eval.eval(seq, doc, serv)
        else:
            if pars['parallel']:
                r = gicdat.jobs.distribute_sequence(seq, doc)
            else:
                r = gicdat.jobs.do_sequence(seq, doc)
        if pars['colate']:
            if pars['colate.annotate'] != None:
                gicdat.jobs.annotate_seq(r, seq, pars['colate.annotate'])
            if pars['colate.indoc']:
                r[pars['colate.indoc']] = doc
            col = gicdat.jobs.Job(pars['colate.xform'], pars['colate.pars'])
            r = col(r)
        out.patch(r)


rename = Rename()
sequence = Sequence()