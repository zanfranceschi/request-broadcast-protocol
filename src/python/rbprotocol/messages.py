# -*- coding: utf-8 -*-

import uuid
import json
import re
from rbprotocol import checktypes


class Message(object):
	def __init__(self):
		self.header = None
		self.body = None

	def to_wire(self):
		header = json.dumps(self.header)
		wired_message = "{}{}{}".format(
			len(header),
			header,
			self.body)
		return wired_message

	@classmethod
	def from_wire(cls, wired_message):
		matches = re.search('^(?P<header_len>[0-9]+)(?P<content>.+)', wired_message)
		header_len = int(matches.group('header_len'))
		content = matches.group('content')
		header = json.loads(content[:header_len])
		body = content[header_len:]
		message = Message()
		message.header = header
		message.body = body
		return message


class HeaderMessage(Message):
	def __init__(self):
		super(HeaderMessage, self).__init__()

	def to_wire(self):
		return json.dumps(self.header)

	@classmethod
	def from_wire(cls, wired_message):
		message = HeaderMessage()
		message.header = json.loads(wired_message)
		return message


class ClientMessage(object):
	pass


class ServerMessage(object):
	pass


class Request(Message, ClientMessage):
	@checktypes(basestring, basestring, buffer)
	def __init__(self, accept, accept_charset, body):
		super(Request, self).__init__()
		self.header = {
			"correlation_id": str(uuid.uuid4()),
			"ack_endpoint": None,
			"ack_timeout": None,
			"accept": accept,
			"accept_charset": accept_charset
		}
		self.body = body


class Ack(HeaderMessage, ServerMessage):
	def __init__(self, request, id):
		super(Ack, self).__init__()
		self.header = {
			"correlation_id": request.header["correlation_id"],
			"id": id
		}


class ResponseHeaderInvitation(HeaderMessage, ClientMessage):
	def __init__(self, request, response_header_endpoint=None, response_header_timeout=None):
		super(ResponseHeaderInvitation, self).__init__()
		self.header = {
			"correlation_id": request.header["correlation_id"],
			"response_header_endpoint": response_header_endpoint,
			"response_header_timeout": response_header_timeout,
		}


class ResponseHeader(HeaderMessage, ServerMessage):
	def __init__(self, response):
		super(ResponseHeader, self).__init__()
		self.header = {
			"correlation_id": response.header["correlation_id"],
			"id": response.header["id"],
			"content_length": response.header["content_length"],
			"content_type": response.header["content_type"]
		}


class ResponseInvitation(HeaderMessage, ClientMessage):
	pass


class ResponseInvitationContinue(ResponseInvitation):
	def __init__(self, request):
		super(ResponseInvitationContinue, self).__init__()
		self.header = {
			"correlation_id": request.header["correlation_id"],
			"status": 100,
			"response_endpoint": None,
			"response_timeout": 0
		}


class ResponseInvitationDontContinue(ResponseInvitation):
	def __init__(self, request):
		super(ResponseInvitationDontContinue, self).__init__()
		self.header = {
			"correlation_id": request.header["correlation_id"],
			"status": 417,
			"response_endpoint": None,
			"response_timeout": 0
		}


class Response(Message, ServerMessage):
	@checktypes(basestring, basestring, basestring, buffer)
	def __init__(self, correlation_id, server_id, content_type, body):
		super(Response, self).__init__()
		self.header = {
			"correlation_id": correlation_id,
			"id": server_id,
			"content_length": len(body),
			"content_type": content_type
		}
		self.body = body
