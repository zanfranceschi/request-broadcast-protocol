# -*- coding: utf-8 -*-

import json
import zmq
from communication_flow import ClientCommunicatonFlow

class ZMQTCPClientCommunicatonFlow(ClientCommunicatonFlow):
	
	def __init__(self, hostname, request_endpoint, ack_timeout, 
		response_header_timeout, response_timeout):

		self.context = zmq.Context.instance()
		self.request_channel = self.context.socket(zmq.PUB)
		self.request_channel.bind(request_endpoint)

		self.ack_channel = self.context.socket(zmq.ROUTER)
		self.response_header_channel = self.context.socket(zmq.ROUTER)
		self.response_channel = self.context.socket(zmq.ROUTER)

		self.hostname = hostname
		self.request_endpoint = request_endpoint
		self.ack_timeout = ack_timeout
		self.response_header_timeout = response_header_timeout
		self.response_timeout = response_timeout

		self._set_aux_channels()


	def _set_aux_channels(self):
		ack_port = self.ack_channel.bind_to_random_port("tcp://*")
		resp_header_port = self.response_header_channel.bind_to_random_port("tcp://*")
		resp_port = self.response_channel.bind_to_random_port("tcp://*")

		self.ack_endpoint = "tcp://{}:{}".format(self.hostname, ack_port)
		self.response_header_endpoint = "tcp://{}:{}".format(self.hostname, resp_header_port)
		self.response_endpoint = "tcp://{}:{}".format(self.hostname, resp_port)

		super(ZMQTCPClientCommunicatonFlow, self).__init__(
			self.request_endpoint,
			self.ack_endpoint,
			self.ack_timeout,
			self.response_header_endpoint,
			self.response_header_timeout,
			self.response_endpoint,
			self.response_timeout)


	def _reset_aux_channels(self):
		self._set_aux_channels()


	def publish_request(self, request_flow, message):
		self.request_flow = request_flow
		self.request_channel.send(message)


	def receive_acks(self, ack_response):
		while (True):
			if (self.ack_channel.poll(self.ack_timeout)):
				responder_ack = self.ack_channel.recv_multipart()
				responder_ack_id = responder_ack[0]
				responder_ack_content = json.loads(responder_ack[1])
				if (responder_ack_content["correlation_id"] == self.request_flow.correlation_id):
					self.request_flow.acks.append(responder_ack_content)
					self.ack_channel.send_multipart(
						[responder_ack_id, ack_response])
			else: break


	def receive_response_headers(self, validate_header, reply_ok, reply_nok):
		while (len(self.request_flow.response_headers) < len(self.request_flow.acks)):
			if (self.response_header_channel.poll(self.response_header_timeout)):
				responder_request_header = self.response_header_channel.recv_multipart()
				responder_request_header_id = responder_request_header[0]
				responder_request_header_content = json.loads(responder_request_header[1])

				if (responder_request_header_content["correlation_id"] == self.request_flow.correlation_id
					and validate_header(responder_request_header_content)):
					self.response_header_channel.send_multipart([responder_request_header_id, reply_ok])
					self.request_flow.response_headers.append(responder_request_header_content)
				else:
					self.response_header_channel.send_multipart([responder_request_header_id, reply_nok])
			else: break
	
	
	def receive_responses(self, on_reponse_received):
		while (len(self.request_flow.responses) < len(self.request_flow.response_headers)):
			if (self.response_channel.poll(self.response_timeout)):
				responder_request = self.response_channel.recv_multipart()
				responder_request_id = responder_request[0]
				responder_request_content = json.loads(responder_request[1])
				
				if (responder_request_content["header"]["correlation_id"] == self.request_flow.correlation_id):
					self.request_flow.responses.append(responder_request_content)
					on_reponse_received(self.request_flow, responder_request_content)
			else: break

		self.ack_channel.unbind(self.ack_channel.LAST_ENDPOINT)
		self.response_header_channel.unbind(self.response_header_channel.LAST_ENDPOINT)
		self.response_channel.unbind(self.response_channel.LAST_ENDPOINT)

		self._reset_aux_channels()