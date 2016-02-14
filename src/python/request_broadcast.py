# -*- coding: utf-8 -*-

"""
Request Broadcast Protocol
"""

import json
import zmq
import uuid


class Request(object):

	def __init__(self, correlation_id, ack_endpoint, ack_timeout, accept, accept_charset, body):
		self.correlation_id = correlation_id
		self.ack_endpoint = ack_endpoint
		self.ack_timeout = ack_timeout
		self.accept = accept
		self.accept_charset = accept_charset
		self.body = body

		self.acks = []
		self.response_headers = []
		self.response_bodies = []	

class RequestFlow(object):

	def __init__(self, correlation_id):
		self.correlation_id = correlation_id
		self.acks = []
		self.response_headers = []
		self.response_bodies = []


class RequestBroadcast(object):

	def __init__(self, hostname, endpoint_port):
		self.hostname = hostname
		self.endpoint_port = endpoint_port
		self.context = zmq.Context.instance()

		self.request_channel = self.context.socket(zmq.PUB)
		self.request_channel.bind("tcp://*:{}".format(self.endpoint_port))

		self.ack_channel = self.context.socket(zmq.ROUTER)
		self.response_header_channel = self.context.socket(zmq.ROUTER)
		self.response_body_channel = self.context.socket(zmq.ROUTER)


	def _send_request(self, request_flow, ack_timeout,
		response_timeout, accept, accept_charset, body):
		
		ack_port = self.ack_channel.bind_to_random_port('tcp://*')

		self.current_request = {
			"header" : {
				"correlation_id" : request_flow.correlation_id,
				"ack_endpoint" : "tcp://{}:{}".format(self.hostname, ack_port),
				"ack_timeout" : ack_timeout,
				"accept" : accept,
				"accept_charset" : accept_charset
			},
			"body" : body
		}

		self.request_channel.send(json.dumps(self.current_request))


	def _receive_acks(self, request_flow, ack_timeout, response_timeout,
		accept, accept_charset, body):
		
		response_header_port = self.response_header_channel.bind_to_random_port('tcp://*')

		ack_response_header = {
			"correlation_id" : request_flow.correlation_id,
			"response_header_endpoint" : "tcp://{}:{}".format(self.hostname, response_header_port),
			"response_header_timeout" : response_timeout,
		}

		while (True):
			if (self.ack_channel.poll(ack_timeout)):
				responder_ack = self.ack_channel.recv_multipart()
				responder_ack_id = responder_ack[0]
				responder_ack_content = json.loads(responder_ack[1])
				if (responder_ack_content["correlation_id"] == request_flow.correlation_id):
					request_flow.acks.append(responder_ack_content)
					self.ack_channel.send_multipart(
						[responder_ack_id, json.dumps(ack_response_header)])
			else:
				break


	def _receive_response_headers(self, request_flow, ack_timeout, response_timeout, 
		accept, accept_charset, body):
		
		
		
		body_response_port = self.response_body_channel.bind_to_random_port('tcp://*')

		header_response_ok = json.dumps({
			"correlation_id" : request_flow.correlation_id,
			"status" : 100,
			"response_body_endpoint" : "tcp://{}:{}".format(self.hostname, body_response_port)
		})

		header_response_nok = json.dumps({
			"correlation_id" : request_flow.correlation_id,
			"status" : 417
		})
		
		while (len(request_flow.response_headers) < len(request_flow.acks)):
			if (self.response_header_channel.poll(response_timeout)):
				responder_request_header = self.response_header_channel.recv_multipart()
				responder_request_header_id = responder_request_header[0]
				responder_request_header_content = json.loads(responder_request_header[1])

				if (responder_request_header_content["correlation_id"] == request_flow.correlation_id):
					self.response_header_channel.send_multipart([responder_request_header_id, header_response_ok])
					request_flow.response_headers.append(responder_request_header_content)
				else:
					self.response_header_channel.send_multipart([responder_request_header_id, header_response_nok])
			else:
				break


	def _receive_response_bodies(self, request_flow, ack_timeout, 
		response_timeout, accept, accept_charset, body, on_reponse_received):
		
		while (len(request_flow.response_bodies) < len(request_flow.response_headers)):
			if (self.response_body_channel.poll(response_timeout)):
				responder_request_body = self.response_body_channel.recv_multipart()
				responder_request_body_id = responder_request_body[0]
				responder_request_body_content = json.loads(responder_request_body[1])
				
				if (responder_request_body_content["header"]["correlation_id"] == request_flow.correlation_id):
					request_flow.response_bodies.append(responder_request_body_content)

				if (on_reponse_received != None):
					on_reponse_received(request_flow, responder_request_body_content)
			else:
				break


	def send(self, ack_timeout, response_timeout,
		accept, accept_charset, body, on_reponse_received = None):

		correlation_id = str(uuid.uuid4())
		request_flow = RequestFlow(correlation_id)

		self._send_request(request_flow, ack_timeout,
			response_timeout, accept, accept_charset, body)

		self._receive_acks(request_flow, ack_timeout,
			response_timeout, accept, accept_charset, body)

		self._receive_response_headers(request_flow, ack_timeout,
			response_timeout, accept, accept_charset, body)

		self._receive_response_bodies(request_flow, ack_timeout,
			response_timeout, accept, accept_charset, body, on_reponse_received)

		self.ack_channel.unbind(self.ack_channel.LAST_ENDPOINT)
		self.response_header_channel.unbind(self.response_header_channel.LAST_ENDPOINT)
		self.response_body_channel.unbind(self.response_body_channel.LAST_ENDPOINT)