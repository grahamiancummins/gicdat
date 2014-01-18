#!/usr/bin/env python -3
# encoding: utf-8

#Created by gic on DATE.

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
from base import Tag


externalDocument_doc = '''
This class specifies the tag type "externalDocument". To be an
externalDocument, a node must 1) have attr 'tag' == 'externalDocument',
have attr 'url' that is a string or unicode.

externalDocument tags are used to link the contents of an additional
resource (for exmaple a second file) into a given document. They recieve
special treatment from the "read" and "write" functions of gicdat.io

'''

externalDocument_t = Tag({'_extern_url': 's'}, info=externalDocument_doc)


