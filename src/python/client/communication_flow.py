# -*- coding: utf-8 -*-

import abc

class RequestFlow(object):

	def __init__(self, correlation_id):
		self.correlation_id = correlation_id
		self.acks = []
		self.response_headers = []
		self.responses = []


class ClientCommunicatonFlow(object):
	__metaclass__ = abc.ABCMeta

	def __init__(self, request_endpoint,
		ack_endpoint, ack_timeout,
		response_header_endpoint, response_header_timeout,
		response_endpoint, response_timeout):

		self.request_endpoint = request_endpoint
		self.ack_timeout = ack_timeout
		self.response_header_timeout = response_header_timeout
		self.response_timeout = response_timeout

		self.ack_endpoint = ack_endpoint
		self.response_header_endpoint = response_header_endpoint
		self.response_endpoint = response_endpoint

	def get_ack_endpoint(self):
		return self.ack_endpoint

	def get_response_header_endpoint(self):
		return self.response_header_endpoint

	def get_response_endpoint(self):
		return self.response_endpoint

	@abc.abstractmethod
	def publish_request(self, request_flow, message):
		pass

	@abc.abstractmethod
	def receive_acks(self, ack_response):
		pass

	@abc.abstractmethod
	def receive_response_headers(self, validate_header, reply_ok, reply_nok):
		pass

	@abc.abstractmethod
	def receive_responses(self, on_reponse_received):
		pass