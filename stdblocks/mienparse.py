#!/usr/bin/env python -3
# encoding: utf-8

#Created by gic on Sun Oct 24 13:45:51 CDT 2010

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

#import xmlparse  
import gicdat.doc
from gicdat.control import report
import numpy as np
from gicdat.base import Parser
from xmlparse import readString, DOT
import zlib, struct, StringIO

DTS = np.ones(1).dtype.str[0]


def readMD(s):
    f = StringIO.StringIO(s)
    dats = {}
    cat = f.read(16)
    while len(cat) == 16:
        pl, hl, dl = struct.unpack("<IIQ", cat)
        path = f.read(pl)
        head = eval(f.read(hl))
        dat = None
        if dl:
            ct = f.read(1)
            if ct in ['<', '>', '|', "{"]:
                ct = ct + f.read(6)
                dti, nd = struct.unpack("<3sI", ct)
                if dti.startswith("{"):
                    dti = dti[1:]
                dti = np.dtype(dti)
            else:
                report("warning, old mdat. May not be platform portable")
                nd = struct.unpack("<I", f.read(4))[0]
                dti = dtype("<" + ct)
            sh = struct.unpack("<" + "Q" * nd, f.read(8 * nd))
            dat = f.read(dl)
            dat = np.fromstring(dat, dti)
            dti = dti.str
            if DTS != dti[0]:
                dtil = np.dtype(DTS + dti[1:])
                dat = dat.astype(dtil)
            dat = np.reshape(dat, sh)
        dats[path] = (dat, head)
        cat = f.read(16)
    return dats


def upath(doc, k):
    els = k.split('.')
    up = []
    b = ''
    for e in els:
        n = e.replace(DOT, '.')
        b = b + e + '.'
        t = doc[b + 'tag']
        up.append("%s:%s" % (t, n))
    return "/" + "/".join(up)


def setdat(doc, k, dat, h):
    for hk in h:
        doc[k + '.' + hk.replace('.', DOT)] = h[hk]
    doc[k + '.' + 'data'] = dat


def deserialize(s):
    l = struct.unpack('<I', s[:4])[0]
    doc = zlib.decompress(s[4:l + 4])
    doc = readString(doc, False)
    s = s[l + 4:]
    try:
        if s:
            try:
                f = readMD(s)
            except:
                s = zlib.decompress(s)
                f = readMD(s)
            des = [k[:-4] for k in doc.find('Data') if k.endswith('.tag')]
            #return doc, f, des
            for de in des:
                try:
                    up = upath(doc, de)
                    try:
                        d, h = f[up]
                    except KeyError:
                        d, h = f[up + '/']
                    setdat(doc, de, d, h)
                except:
                    report("can't find data for element %s" % (de,))
                    raise
    except:
        raise
        report("cant load data")
    return doc


class MienParse(Parser):
    '''
    Read mien files

    '''

    canread = ('application/com.symbolscope.mien',)
    canwrite = ()
    extensions = {'mien': 'application/com.symbolscope.mien'}


    def read(self, stream, filetype, **kw):
        mdoc = deserialize(stream.read())
        return (mdoc, None)


mien_p = MienParse()

