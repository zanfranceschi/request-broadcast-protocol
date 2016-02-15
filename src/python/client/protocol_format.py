# -*- coding: utf-8 -*-

import json

class ClientFormat(object):
	""" Defines message formats used by the the Client """

	def __init__(self, correlation_id):
		self.correlation_id = correlation_id

	def request(self, ack_endpoint, ack_timeout, accept_charset, body):
		return json.dumps({
			"header" : {
				"correlation_id" : self.correlation_id,
				"ack_endpoint" : ack_endpoint,
				"ack_timeout" : ack_timeout,
				"accept_charset" : accept_charset
			},
			"body" : body
		})

	def ack_response(self, response_header_endpoint, response_header_timeout):
		return json.dumps({
			"correlation_id" 			: self.correlation_id,
			"response_header_endpoint" 	: response_header_endpoint,
			"response_header_timeout" 	: response_header_timeout,
		})

	def response_header_ok(self, response_endpoint):
		return json.dumps({
			"correlation_id" : self.correlation_id,
			"status" : 100,
			"response_endpoint" : response_endpoint
		})

	def response_header_nok(self):
		return json.dumps({
			"correlation_id" : self.correlation_id,
			"status" : 417
		})

