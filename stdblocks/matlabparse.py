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
from __future__ import print_function, unicode_literals

from gicdat.base import Parser
import gicdat.enc
import mat2py, gicdat.doc, numpy, gicdat.control


class MatParse(Parser):
    '''
    Handles Matlab v7 files (at least, most of them. Doesn't currently handle
    sparse arrays
    '''

    canread = ("application/matlab-mat",)
    canwrite = ("application/matlab-mat",)
    extensions = {"mat": "application/matlab-mat"}

    def read(self, stream, filetype, **kw):
        d = mat2py.read(stream)
        return (gicdat.doc.Doc(d), None)

    def write(self, d, stream, filetype, **kw):
        '''
        d is a dictionary of gicdat.doc.Node instances, of the sort returned by
        gicdat.Doc.allNodes(). Stream is a file-like object open in write mode.
        filetype is a mime-type-like string. kw args are implementation
        specific

        Write should return None
        '''
        mat2py.write(stream, d)


mat_p = MatParse()
