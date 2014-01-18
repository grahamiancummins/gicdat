#!/usr/bin/env python
# encoding: utf-8

#Created by gic on Thu Oct 21 07:39:23 CDT 2010

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
import numbers, types, numpy, re

gdtypes = {'s': unicode, 'i': int, ' ': lambda x: x,
           "#": numpy.array, 'x': float, 'z': complex, '[': tuple}
simpletypes = 'si xz'
DOT = "_0_"


def classify(v):
    '''
    Return a one character string representing the generalized type of a value v.
    These are:
        s    - string types
        x    - real number types
        i    - integer number types (including Boolean)
        z    - complex numbers
        [    - 1D sequence types (list and tuple)
        {    - dictionary types (including gicdat.doc.Doc)
        #    - numpy ndarrays
        ' '  - (a space character) None
        ?    - other types (which are generally not supported by gicdat
    the module dictionary gdtypes maps most of these strings to the
    "standard" examples of their group (e.g 'x':float). Generally
    gdtypes[classify(x)](x) can be used to cast a value to its standard type. Note
    that to support this idiom, gdtypes["#"], and gdtypes[' '] are not set to the
    associated type objects (numpy.ndarray, and types.NoneType), since these types
    can't be used in the expected way as constructors. "#" references numpy.array,
    which is a specialized constructor that generally does cast sequences to array type
    in the expected way. " " references an identity function, so it doesn't cast values
    (there is no constructor for None instances), the casting idiom will return None for
    an input of None, as expected.
    '''
    if v is None:
        return ' '
    t = type(v)
    if t in [str, unicode, numpy.string_]:
        return 's'
    if t == float:
        return 'x'
    if t in [int, long, bool]:
        return 'i'
    if t == complex:
        return 'z'
    if t in [list, tuple]:
        return '['
    if isinstance(v, dict):
        return '{'
    if isinstance(v, numpy.ndarray):
        return '#'
    if isinstance(v, numbers.Number):
        if isinstance(v, numbers.Integral):
            return 'i'
        if isinstance(v, numbers.Real):
            return 'x'
        return 'z'
    return '?'


def pattern(z):
    '''
    Returns a Pattern instance based on z.

    if Z is already a Pattern instance, this function simply returns it.
    Otherwise, it converts z, recursively if appropriate (it descends into
    dict and sequence arguments)

    Convertible values include: dict, tuple, list, Number, string,

    Dicts X are converted to DictPattern(z)

    Sequences are converted to SeqPattern(z)

    Number instances are converted to Pattern(z)

    Strings that begin with "=" are converted to Pattern(s[1:]) (e.g. match the
    literal string, minus the leading equals.

    Strings that begin with ":" are converted to RePattern(s[1:]), which uses the
    string (minus the leading ":") as a regular expression.

    Strings that begin with ";" are converted to RePattern(s[1:], True, True),
    (case insensitive, ignore leading and trailing space).

    Strings that don't begin with one of these characters, and contain one or more "||"
    are converted to OrPattern([pattern(s) for s in z.split("||")])

    All other strings are converted to TypePattern(z)
    '''

    if isinstance(z, Pattern):
        return z
    t = classify(z)
    if t == "{":
        z = dict([(k, pattern(z[k])) for k in z])
        return DictPattern(z)
    elif t == "[":
        z = [pattern(k) for k in z]
        return SeqPattern(z)
    elif t == 's':
        if z.startswith('='):
            return Pattern(z[1:])
        elif z.startswith(':'):
            return RePattern(z[1:])
        elif z.startswith(';'):
            return RePattern(z[1:], True, True)
        elif "||" in z:
            return OrPattern([pattern(s) for s in z.split("||")])
        else:
            return TypePattern(z)
    elif t in 'xiz ':
        return Pattern(z)
    else:
        raise TypeError('object of type %s cant be interpretted as a search pattern' % (str(type(z))))


def altern(*args):
    return OrPattern([pattern(s) for s in args])


def match(val, pat, ns={}, conditions=[]):
    return pattern(pat).match(val, ns, conditions)


class MatchFailure(Exception):
    pass


class Pattern(object):
    '''
    A class that implements pattern matching.

    This base class provides the required methods for the Pattern API, which include exposing the methods
    __eq__ and match.

    Subclasses will want to overload match_in, which is used internally to determine if a value matches the
    stored target. This base class assumes the target to be a literal, simple, value, and checks for a match
    using the built in "==".
    '''

    def __init__(self, p):
        self.p = p
        self.fail = None

    def __str__(self):
        return str(self.p)

    def match_in(self, v, ns):
        if not self.p == v:
            raise MatchFailure("%s != %s" % (self.p, v))
        return (ns, [])

    def match(self, v, ns, conds):
        self.fail = None
        try:
            ns, nconds = self.match_in(v, ns)
            self.checkconds(conds + nconds, ns)
            ns['_matched'] = True
            return ns
        except MatchFailure as mf:
            self.fail = mf
            return False

    def __eq__(self, v):
        return self.match(v, {}, [])

    def checkconds(self, conds, ns):
        for c in conds:
            try:
                v = eval(c, {'np': numpy}, ns)
            except NameError:
                raise MatchFailure("Unbound names in condition %s" % c)
            if not v:
                raise MatchFailure("Conditions %s failed" % c)


class DictPattern(Pattern):
    '''
    A DictPattern is equal to a target if the target is a dict instance and for each
    key that is present in the DictPattern self[key] matches target.get(key).
    '''

    def match_in(self, v, ns):
        if not isinstance(v, dict):
            raise MatchFailure("DictPattern target (of type %s) isn't a dict instance" % (type(v),))
        conds = []
        for k in self.p:
            ns, nconds = self.p[k].match_in(v.get(k), ns)
            conds = conds + nconds
        return (ns, conds)


class SeqPattern(Pattern):
    '''
    A SeqPattern matches any other 1D sequence, if it has the same length and the
    values match (ndarrays may match a SeqPattern, but only if they have
    exactly 1 dimension)
    '''

    def checkseq(self, v):
        if not hasattr(v, '__len__') or not hasattr(v, '__getitem__'):
            raise MatchFailure("SeqPattern target (of type %s) isn't a sequence" % (type(v),))
        if len(v) > 0:
            try:
                bool(v[0] == 0)
            except ValueError:
                raise MatchFailure(
                    "SeqPattern target has values that don't support bool(==). Probably it is numpy array of dimension >1")

    def match_in(self, v, ns):
        self.checkseq(v)
        if len(v) != len(self.p):
            raise MatchFailure("SeqPattern target is length %i. Needs to be %i" % (len(v), len(self.p)))
        conds = []
        for i in range(len(self.p)):
            ns, nconds = self.p[i].match_in(v[i], ns)
            conds = conds + nconds
        return (ns, conds)


class RePattern(Pattern):
    '''
    Match a regular expression. __init__ takes a string to compile into the expression, and two flags,
    nocase and strip. If nocase is true, the expression is compiled case-insensitive. If strip is true,
    the match ignores leading and trailing whitespace.
    '''

    def __init__(self, p, nocase=False, strip=False):
        flags = 0
        if nocase:
            flags = re.I
        self.s = p
        self.p = re.compile(p, flags)
        self.strip = strip

    def __str__(self):
        return self.s

    def match_in(self, v, ns):
        tv = type(v)
        if not tv in [str, unicode]:
            raise MatchFailure('RePattern target of type %s needs to be string or unicode' % (tv,))
        if self.strip:
            v = v.strip()
        m = self.p.match(v)
        if not m:
            raise MatchFailure('%s !~= %s' % (self.s, v))
        return (ns, [])


class OrPattern(Pattern):
    '''
    Matches alternation. The argument is a list of other patterns, and if any of these match, the match
    succeeds (namespace bindings and conditions are applied only for the branch that matched)
    '''

    def __str__(self):
        return "||".join([str(s) for s in self.p])

    def match_in(self, v, ns):
        nns = {}
        nns.update(ns)
        for pat in self.p:
            try:
                nns, nconds = pat.match_in(v, nns)
                return (nns, nconds)
            except:
                pass
        raise MatchFailure('No branches of OrPattern %s match' % (str(self),))


class TypePattern(Pattern):
    lbind = re.compile("^([A-Z]+)\s+of")
    '''
    Pattern based on a string, which specifies loose pattern matching.

    _		- matches anything (except None)
    x		- matches anything of genaralized type float (this works for any type specifier)
            recognized by classify. You may also use combinations of letters from this set,
            to match more than one type. For example, "ix" and "ixz" are common, since "x"
            will match only a number with is float, but which is _not_ int.
    z?      - if z is any type pattern, matches z, and also matches None
    X 		- matches any simple value, and stores the result as X in the search namespace
              (subsequently, the tpattern X will only match the stored value). This applys
              to any upper case letter
    X of x	- matches anything of general type float and stores the result as X
             (works for any upper case letter and type specifier)
    4-[     - Matches a 1D sequence type of length 4
    N-[     - Matches a 1D sequence type, and stores its length as N
    3,2,4-# - Matches an ndarray of shape (3,2,4)
    N,2-#   - Matches any 2D array with shape[1]==2, and stores shape[1] as N
    [ of x  - Matches a 1D sequence where all the elements are generalized float type
              this works for any type spec, including variants of [ and #, and can
              be combined with length constraints, so for example:
              N-[ of N-[ matches a 2D square matrix, stored as a list of lists (since the
              outer N is stored in the namespace, the inner N will only match in this case
              if the length of every contained list is the same as the length of the outer
              list

               NOTE: "X of 3,2-#" and the like are legal, but may be dangerous. Other predicates
               attempting to bind X to a simple value will invoke the dreaded:
               ValueError: The truth value of an array with more than one element is ambiguous.
               Make sure the whole pattern scope using this value ONLY for the array, and make
               sure to write your conditions using numpy-friendly syntax (eg. (X>0).all(), not
               X>0). You have access to the numpy module in the conditions under the name "np"

    3,2,.-#
    .,3-#   - Matches an ND array with any number of dimensions, in which the size of the
            first (or last) dimensions are constrained. The "." matches any number of
            dimensions of any size
    s::c		- The string s is used as the pattern, and the string c is used as a condition.
            This is a string which can be evaluated in python, given the current match namespace,
            and returns a boolean value (e.g "X<10&X>Y")

    '''

    def __init__(self, p):
        if "::" in p:
            p, c = p.split("::")
            self.conditions = [c]
        else:
            self.conditions = []
        self.s = p
        self.typeconst = None
        self.shapeconst = None
        self.seqtype = None
        self.bind = None
        self.parse(p)

    def parse(self, p):
        p = p.strip()
        m = self.lbind.match(p)
        if m:
            self.bind = m.groups()[0]
            p = p[m.end():].strip()
        if p == "_":
            pass
        elif p.isupper():
            self.bind = p
        elif "#" in p:
            self.typeconst = "#"
            if 'of' in p:
                z = p.split('of')
                p = z[0]
                self.seqtype = z[1].strip()
            if '-' in p:
                sc = p.split('-')[0].split(',')
                self.shapeconst = []
                for sc in p.split('-')[0].split(','):
                    try:
                        sc = int(sc)
                    except:
                        pass
                    self.shapeconst.append(sc)
        elif "[" in p:
            self.typeconst = '['
            if 'of' in p:
                z = p.split('of')
                p = z[0]
                self.seqtype = TypePattern('of'.join(z[1:]))
            if '-' in p:
                sc = p.split('-')[0].strip()
                if sc.isupper():
                    self.shapeconst = sc
                else:
                    self.shapeconst = int(sc)
        elif all([e in simpletypes for e in p]):
            self.typeconst = p
        else:
            raise ValueError("Can't parse TypePattern %s" % p)

    def __str__(self, ):
        if self.conditions:
            return self.s + "::" + self.conditions[0]
        else:
            return self.s

    def dobind(self, k, v, ns):
        if k in ns:
            if v != ns[k]:
                raise MatchFailure("Attempt to bind %s to %s, but it already has value %s" % (k, v, ns[k]))
        else:
            ns[k] = v

    def shapecheck(self, v, ns):
        if self.typeconst == '[':
            lv = len(v)
            if type(self.shapeconst) == int:
                if lv != self.shapeconst:
                    raise MatchFailure("Target length is %i, and needs to be %i" % (lv, self.shapeconst))
            else:
                self.dobind(self.shapeconst, lv, ns)
        else:
            vs = v.shape
            sc = self.shapeconst
            if sc[0] == '.':
                sc = sc[1:]
                vs = vs[-len(sc):]
            elif sc[-1] == '.':
                sc = sc[:-1]
                vs = vs[:len(sc)]
            for i in range(len(sc)):
                if type(sc[i]) == int:
                    if vs[i] != sc[i]:
                        raise MatchFailure("Target shape is %s, and needs to match %s" % (v.shape, self.shapeconst))
                else:
                    self.dobind(sc[i], vs[i], ns)


    def seqcheck(self, v, ns):
        if self.typeconst == '[':
            for e in v:
                self.seqtype.match_in(e, ns)
        else:
            if v.size:
                ve = v.flat[0]
            else:
                ve = numpy.zeros(1, v.dtype)[0]
            vt = classify(ve)
            if vt != self.seqtype:
                raise MatchFailure("Target's generalized type is %s, needed %s" % (vt, self.seqtype))


    def match_in(self, v, ns):
        if v is None:
            raise MatchFailure("TypePattern target is None")
        if self.typeconst:
            vt = classify(v)
            if not vt in self.typeconst:
                raise MatchFailure("TypePattern target is generalized type %s, needed %s" % (vt, self.typeconst))
        if self.shapeconst:
            self.shapecheck(v, ns)
        if self.seqtype:
            self.seqcheck(v, ns)
        if self.bind:
            self.dobind(self.bind, v, ns)
        return (ns, self.conditions)


def seqtype(t):
    l = len(t)
    if not l:
        return "0-["
    st = "%i-[ of " % l
    if not l:
        return st
    ct = set([classify(x) for x in t])
    if len(ct) > 1 or list(ct)[0] != "[":
        return st + ''.join(list(ct))
    lens = [len(s) for s in t]
    st += "%i-to %i-[ of " % (min(lens), max(lens))
    types = [classify(s[0]) for s in t if len(s)]
    types = ''.join(list(set(types)))
    st += types
    return st


def whynot(pat, targ):
    pass


def contains(pat1, pat2):
    pass


def whynotcontains(pat1, pat2):
    pass


def whazzat(val):
    pass