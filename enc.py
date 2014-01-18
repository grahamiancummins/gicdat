#!/usr/bin/env python -3
# encoding: utf-8

#Created by gic on Fri Oct 22 15:04:33 CDT 2010

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
import binascii, json
import numpy as np
import zipfile, StringIO
from doc import Doc, astuple
from search import DOT, classify, simpletypes
#import numbers

def flatiter(a):
    its = []
    its.insert(0, a.__iter__())
    while True:
        try:
            v = its[0].next()
        except StopIteration:
            its.pop(0)
            if its:
                continue
            else:
                raise
        if hasattr(v, '__iter__'):
            its.insert(0, v.__iter__())
        else:
            sr = (yield v)


def flat(c):
    return [v for v in flatiter(c)]


def tshape(t):
    if not type(t) == tuple:
        return None
    if len(t) == 0:
        return ((0,), ())
    if all([type(a) == tuple for a in t]):
        td = tshape(t[0])
        if td == None:
            return None
        td, ty = td
        if len(ty) > 1:
            return None
        tdlr = (td[-1], td[-1])
        for tt in t[1:]:
            ttd = tshape(tt)
            if ttd == None:
                return None
            ttd, tty = ttd
            if tty != ty:
                if ty == ():
                    ty = tty
                elif tty == ():
                    pass
                else:
                    return None
            if len(ttd) != len(td):
                return None
            if any([td[i] != ttd[i] for i in range(len(td) - 1)]):
                return None
            if type(td[-1]) == tuple:
                ttdlr = ttd[-1]
            else:
                ttdlr = (ttd[-1], ttd[-1])
            tdlr = (min(tdlr[0], ttdlr[0]), max(tdlr[1], ttdlr[1]))
        if tdlr[0] != tdlr[1]:
            td = td[:-1] + (tdlr,)
        return ((len(t),) + td, ty)
    elif any([not classify(a) in simpletypes for a in t]):
        return None
    else:
        z = [type(a) for a in t]
        if len(set(z)) == 1:
            z = (z[0],)
        return ((len(t),), tuple(z))


def rtcoords(t):
    its = []
    its.insert(0, (t.__iter__(), [-1]))
    while True:
        try:
            v = its[0][0].next()
            its[0][1][-1] += 1
        except StopIteration:
            its.pop(0)
            if its:
                continue
            else:
                raise
        if hasattr(v, '__iter__'):
            its.insert(0, (v.__iter__(), its[0][-1] + [-1] ))
        else:
            sr = (yield tuple(its[0][1]), v)


def asarray(t, fill=np.nan):
    ts = tshape(t)
    if ts == None:
        t = astuple(t)
        ts = tshape(t)
    if ts == None:
        raise RuntimeError('Attempt to convert an unsafe tuple to array')
    if len(ts[1]) > 1:
        return np.array(t, np.object)
    ragged = type(ts[0][-1]) == tuple
    if not ragged:
        a = np.array(t)
    else:
        s = ts[0][:-1] + (ts[0][-1][-1],)
        ty = ts[1][0]
        q = ty(1.0)
        aty = np.array([q]).dtype
        a = np.ones(s, aty) * fill
        for co, v in rtcoords(t):
            a[co] = v
    return a


def a2t(doc):
    for k in doc.keys(-1, None, True, False):
        v = doc[k]
        if classify(v) == "#":
            doc[k] = astuple(v)


def t2a(doc):
    for k in doc.keys(-1, None, True, False):
        v = doc[k]
        if classify(v) == "[":
            try:
                a = asarray(v)
            except:
                continue
            doc[k] = a


def distribute(a, f):
    if hasattr(a, '__iter__'):
        return tuple([distribute(i, f) for i in a])
    else:
        return f(a)


def trange(a):
    minv = np.inf
    maxv = -np.inf
    for v in flatiter(a):
        minv = min(minv, v)
        maxv = max(maxv, v)
    return (minv, maxv)


def doc2dict(doc, enc=None):
    '''
    '''
    d = {}
    for k in doc.keys(-1):
        if type(doc[k]) == np.ndarray:
            d[k] = a2d(doc[k], enc)
        elif type(doc[k]) == Doc:
            pass
        else:
            d[k] = doc[k]
    return d


def dict2doc(d, data=None, safe=False):
    for k in d:
        if type(d[k]) == dict:
            d[k] = d2a(d[k], data)
    return Doc(d, safe)


def dictcleanup(d):
    keys = sorted(d, cmp=lambda x, y: cmp(len(x), len(y)))
    clean = []
    for i, k in enumerate(keys):
        ks = k + '.'
        for k2 in keys[i + 1:]:
            if k2.startswith(ks):
                clean.append(k)
                break
    for k in clean:
        d[k + '._'] = d[k]
        del (d[k])


def flatten(d, copy=False):
    '''

    '''
    if copy:
        d = d.copy()
    fd = {}
    for k in d.keys(-1):
        if not type(d[k]) == Doc:
            fd[k] = d[k]
    return fd


def a2d(a, encoding=None):
    '''
    Convert an array to a dictionary. This results in a dictionary with three
    keys. The first two are always 'shape':a.shape, and 'dtype':a.dtype.str.
    The last depends on "encoding". If encoding is None, this key is
    "raw":a.tostring(). If  encoding is "base64" this results in
    'base64:binascii.b2a_base64(a.tostring()). If "encoding" is a list
    instance, then the raw data string is appended to this list, and the data
    dictionary gets a key "index", which is set to the index of the data in the
    list. If encoding is file-like, then the raw data string is written to this
    file, and the dictionary gets a key "offset"

    '''
    d = {'shape': a.shape, 'dtype': a.dtype.str}
    if isinstance(encoding, list):
        d['index'] = len(encoding)
        encoding.append(a.tostring())
    elif not encoding:
        d['raw'] = a.tostring()
    elif encoding == 'base64':
        d['base64'] = binascii.b2a_base64(a.tostring())
    elif hasattr(encoding, 'tell'):
        d['offset'] = encoding.tell()
        encoding.write(a.tostring())
    return d


def d2a(d, datasource=''):
    '''
    Convert a dictionary to an ndarray
    d should have keys 'shape' (tuple) and 'dtype' (str) as described for
    a2dict. The remaining key may be "raw", "base64" or "offset". If it is
    "offset" then datasource should be passed as well, and should be either a
    string or a file like object containing the data, which should start at the
    location specifed by "offset". If it is 'index', then datasource should be
    a list or array, and datasource[d['index']] is used as the raw data.

    '''
    dtype = np.dtype(str(d['dtype']))
    shape = tuple(d['shape'])
    if 'raw' in d:
        rawdat = str(d['raw'])
    elif 'base64' in d:
        rawdat = binascii.a2b_base64(d['base64'])
    elif 'index' in d:
        rawdat = datasource[d['index']]
    elif 'offset' in d:
        os = d['offset']
        nbts = dtype.itemsize * np.multiply.reduce(d['shape'])
        if hasattr(datasource, 'seek'):
            datasource.seek(os)
            rawdat = datasource.read(nbts)
        else:
            rawdat = datasource[os:os + nbts]
    a = np.reshape(np.fromstring(rawdat, dtype), shape)
    return a


class DocEncoder(json.JSONEncoder):
    def default(self, obj):
        if type(obj) == np.ndarray:
            return obj.tolist()
        elif isinstance(obj, np.number):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            else:  #np.complexfloating
                return complex(obj)
            #		elif isinstance(obj, numbers.Number) and not type(obj) in [int, float, complex]:
            #			if isinstance(obj, numbers.Integral):
            #				return int(obj)
            #			elif isinstance(obj, numbers.Real):
            #				return float(obj)
            #			else:
            #				return complex(obj)
            #		else:
            #			print(obj)
        return json.JSONEncoder.default(self, obj)


def tojson(doc, stream=None):
    if stream:
        json.dump(doc, stream, cls=DocEncoder)
    else:
        return json.dumps(doc, cls=DocEncoder)


def fromjson(stream, asdoc=True):
    if type(stream) in [str, unicode]:
        d = json.loads(stream)
    else:
        d = json.load(stream)
    if asdoc:
        return Doc(d)
    else:
        return d


def tozip(doc, stream=None):
    if not stream:
        stre = StringIO.StringIO()
        tozip(doc, stre)
        s = stre.getvalue()
        stre.close()
        return s
    else:
        z = zipfile.ZipFile(stream, 'w')
        dstr = StringIO.StringIO()
        d = doc2dict(doc, dstr)
        z.writestr('doc.py', repr(d))
        z.writestr('data.raw', dstr.getvalue())
        dstr.close()


def fromzip(stream):
    if type(stream) in [str, unicode]:
        stre = StringIO.StringIO(stream)
        doc = fromzip(stre)
    else:
        z = zipfile.ZipFile(stream, 'r')
        rdat = z.read('data.raw')
        dd = eval(z.read('doc.py'))
        doc = dict2doc(dd, rdat, False)
    return doc

