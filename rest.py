	#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2009-07-15.

# Copyright (C) 2009 Graham I Cummins
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

import urllib2
from gicdat.control import report

class PutRequest(urllib2.Request):
	def get_method(self):
		return "PUT"

class DeleteRequest(urllib2.Request):
	def get_method(self):
		return "DELETE"

class Resource(object):
	def __init__(self, url, authrealm = None, uname=None, passwd = None, ctype='text/plain'):
		self.url = url
		self.ctype = ctype
		if not authrealm:
			self.opener = urllib2.build_opener(urllib2.HTTPHandler)
		else:
			if authrealm == "Basic":
				authhandler = urllib2.HTTPBasicAuthHandler()
				authhandler.add_password(None, url, uname, passwd)
			else:
				authhandler = urllib2.HTTPDigestAuthHandler()
				authhandler.add_password(authrealm, url, uname, passwd)
			self.opener = urllib2.build_opener(authhandler)
		
	def build_request(self, verb, path,  headers, payload=None):
		url = self.url + path
		if verb == 'put':
			req = PutRequest(url)
		elif verb == 'delete':
			req = DeleteRequest(url)
		else:
			req = urllib2.Request(url)
		if payload:
			req.add_data(payload)
			cl =  len(payload)
			req.add_header("Content-Length", cl)
		for k in headers:
			req.add_header(k, headers[k])
		return req
	
	def send_request(self, verb, path, payload=None, ctype=None, headers=None):
		if not headers:
			headers = {}
		if not 'Accept' in headers:
			headers['Accept']=self.ctype
		if ctype:
			if verb == "get":
				headers['Accept'] = ctype
			else:
				headers['Content-Type'] = ctype	
		req = self.build_request(verb, path, headers, payload)
		try:
			s = self.opener.open(req).read()
		except urllib2.HTTPError, e:
			s = "ERROR %i:" % e.code + e.read()
			report(s)
			if 'www-authenticate' in e.hdrs:
				report('Authentication required: %s' % e.hdrs['www-authenticate'])
		return s

	def get(self, path, ctype =None, headers=None):
		return self.send_request('get', path, None, ctype, headers)

	def post(self, path, payload, ctype=None, headers=None):
		return self.send_request("post", path, payload, ctype, headers) 

	def put(self, path, payload, ctype =None,headers=None):
		return self.send_request("put", path, payload, ctype, headers) 

	def delete(self, path):
		return self.send_request("delete", path, None, None, None) 

#be careful with the "/" on path and urlname. "//" and trailing "/" are not ignored 


		
