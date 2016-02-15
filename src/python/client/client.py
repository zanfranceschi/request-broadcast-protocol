# -*- coding: utf-8 -*-

import json
import uuid
from protocol_format import ClientFormat
from communication_flow import RequestFlow
from zmq_communication_flow import ZMQTCPClientCommunicatonFlow


class Client(object):

	def __init__(self, hostname, request_endpoint, ack_timeout,
		response_header_timeout, response_timeout):
		self.ack_timeout = ack_timeout
		self.response_header_timeout = response_header_timeout
		self.response_timeout = response_timeout

		self.communication = ZMQTCPClientCommunicatonFlow(
			hostname,
			request_endpoint, 
			self.ack_timeout, 
			self.response_header_timeout, 
			self.response_timeout)


	def request(self, payload, validate_header, on_reponse_received):
		correlation_id = str(uuid.uuid4())
		request_flow = RequestFlow(correlation_id)
		_format = ClientFormat(correlation_id)
		
		request = _format.request(
			self.communication.get_ack_endpoint(),
			self.ack_timeout, 
			"utf-8",
			payload)

		self.communication.publish_request(request_flow, request)

		ack_response = _format.ack_response(
			self.communication.get_response_header_endpoint(),
			self.response_header_timeout)

		self.communication.receive_acks(ack_response)

		response_header_ok = _format.response_header_ok(
			self.communication.get_response_endpoint())

		response_header_nok = _format.response_header_nok()

		self.communication.receive_response_headers(
			validate_header,
			response_header_ok,
			response_header_nok)

		self.communication.receive_responses(on_reponse_received)


	