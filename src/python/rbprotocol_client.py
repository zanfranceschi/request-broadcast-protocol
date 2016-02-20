#!/home/zanfranceschi/Projects/request-broadcast-protocol/src/python/virtenv/bin/python
# -*- coding: utf-8 -*-

import abc
import zmq
import uuid
import json

class RequestProcess(object):
	def __init__(self):
		self.correlation_id = None
		self.request_content = None
		self.hostname = None
		self.ack_socket = None
		self.ack_endpoint = None
		self.ack_timeout = None
		self.ack_responses = []
		self.response_header_socket = None
		self.response_header_endpoint = None
		self.response_header_timeout = None
		self.response_header_responses = []
		self.response_content_socket = None
		self.response_content_endpoint = None
		self.response_content_timeout = None
		self.response_content_responses = []


class ClientRequestStep(object):
	__metaclass__ = abc.ABCMeta

	def __init__(self):
		self.next = None

	def set_next(self, step):
		self.next = step

	@abc.abstractmethod
	def handle(self, request_process):
		pass


class SetDynamicEndpoints(ClientRequestStep):
	def __init__(self, hostname):
		super(SetDynamicEndpoints, self).__init__()
		self.hostname = hostname
		self.context = zmq.Context.instance()
		self.ack_socket = self.context.socket(zmq.ROUTER)
		self.response_header_socket = self.context.socket(zmq.ROUTER)
		self.response_content_socket = self.context.socket(zmq.ROUTER)
		self.ack_endpoint = None
		self.response_header_endpoint = None
		self.response_content_endpoint = None

	def _prepare_for_new_request(self, hostname, socket, endpoint):
		if (socket.LAST_ENDPOINT): socket.unbind(socket.LAST_ENDPOINT)
		port = socket.bind_to_random_port("tcp://*")
		setattr(self, endpoint, "tcp://{}:{}".format(hostname, port))

	def handle(self, request_process):
		request_process.hostname = self.hostname
		self._prepare_for_new_request(request_process.hostname, self.ack_socket, 'ack_endpoint')
		self._prepare_for_new_request(request_process.hostname, self.response_header_socket, 'response_header_endpoint')
		self._prepare_for_new_request(request_process.hostname, self.response_content_socket, 'response_content_endpoint')
		request_process.ack_socket = self.ack_socket
		request_process.ack_endpoint = self.ack_endpoint
		request_process.response_header_socket = self.response_header_socket
		request_process.response_header_endpoint = self.response_header_endpoint
		request_process.response_content_socket = self.response_content_socket
		request_process.response_content_endpoint = self.response_content_endpoint
		if (self.next): self.next.handle(request_process)


class SetTimeouts(ClientRequestStep):
	def __init__(self,
		ack_timeout,
		response_header_timeout,
		response_content_timeout):
		super(SetTimeouts, self).__init__()
		self.ack_timeout = ack_timeout
		self.response_header_timeout = response_header_timeout
		self.response_content_timeout = response_content_timeout
	
	def handle(self, request_process):
		request_process.ack_timeout = self.ack_timeout
		request_process.response_header_timeout = self.response_header_timeout
		request_process.response_content_timeout = self.response_content_timeout
		if (self.next): self.next.handle(request_process)


class RequestBroadcast(ClientRequestStep):
	def __init__(self, port):
		super(RequestBroadcast, self).__init__()
		self.context = zmq.Context.instance()
		self.request_socket = self.context.socket(zmq.PUB)
		self.request_socket.bind("tcp://*:{}".format(port))

	def handle(self, request_process):
		request_process.correlation_id = str(uuid.uuid4())
		request_header = json.dumps({
			"correlation_id" : request_process.correlation_id,
			"ack_endpoint" : request_process.ack_endpoint,
			"ack_timeout" : request_process.ack_timeout,
			"accept_charset" : "utf-8"
		})
		request_process.request_content
		self.request_socket.send_multipart([request_header, request_process.request_content])
		if (self.next): self.next.handle(request_process)


class ReceiveRespondAcks(ClientRequestStep):
	def __init__(self):
		super(ReceiveRespondAcks, self).__init__()

	def handle(self, request_process):
		ack_response = json.dumps({
			"correlation_id" 			: request_process.correlation_id,
			"response_header_endpoint" 	: request_process.response_header_endpoint,
			"response_header_timeout" 	: request_process.response_header_timeout,
		})
		while (True):
			if (request_process.ack_socket.poll(request_process.ack_timeout)):
				ack_responder = request_process.ack_socket.recv_multipart()
				ack_responder_id = ack_responder[0]
				ack_responder_content = json.loads(ack_responder[1])
				if (ack_responder_content["correlation_id"] == request_process.correlation_id):
					request_process.ack_responses.append(ack_responder_content)
					request_process.ack_socket.send_multipart(
						[ack_responder_id, ack_response])
			else: break
		if (self.next): self.next.handle(request_process)


class ReceiveRespondResponseHeaders(ClientRequestStep):
	def __init__(self, validate_header):
		super(ReceiveRespondResponseHeaders, self).__init__()
		self.validate_header = validate_header

	def handle(self, request_process):
		response_header_response_ok = json.dumps({
			"correlation_id" : request_process.correlation_id,
			"status" : 100,
			"response_content_endpoint" : request_process.response_content_endpoint
		})
		response_header_response_nok = json.dumps({
			"correlation_id" : request_process.correlation_id,
			"status" : 417
		})
		while (len(request_process.response_header_responses) < len(request_process.ack_responses)):
			#response_header_response = None
			if (request_process.response_header_socket.poll(request_process.response_header_timeout)):
				response_header_responder = request_process.response_header_socket.recv_multipart()
				response_header_responder_id = response_header_responder[0]
				response_header_responder_content = json.loads(response_header_responder[1])
				if (response_header_responder_content["correlation_id"] == request_process.correlation_id 
						and self.validate_header(response_header_responder_content)):
					request_process.response_header_responses.append(response_header_responder_content)
					response_header_response = response_header_response_ok
				else:
					response_header_response = response_header_response_nok
				request_process.response_header_socket.send_multipart([response_header_responder_id, response_header_response])
			else: break
		if (self.next): self.next.handle(request_process)


class ReceiveResponseContents(ClientRequestStep):
	def __init__(self, on_reponse_received = None):
		super(ReceiveResponseContents, self).__init__()
		self.on_reponse_received = on_reponse_received

	def handle(self, request_process):
		while (len(request_process.response_content_responses) < len(request_process.ack_responses)):
			if (request_process.response_content_socket.poll(request_process.response_content_timeout)):
				response_content_responder = request_process.response_content_socket.recv_multipart()
				response_content_responder_id = response_content_responder[0]
				response_content_responder_header = json.loads(response_content_responder[1])
				response_content_responder_content = response_content_responder[2]
				if (response_content_responder_header["correlation_id"] == request_process.correlation_id):
					request_process.response_content_responses.append(response_content_responder)
					if (self.on_reponse_received): self.on_reponse_received(response_content_responder)
			else: break
		if (self.next): self.next.handle(request_process)


import pprint

def validate_header(content):
	return True

pp = pprint.PrettyPrinter(indent=4)

def on_reponse_received(response):
	pp.pprint(json.loads(response[2]))

step1 = SetDynamicEndpoints("localhost")
step2 = SetTimeouts(10, 5000, 5000)
step3 = RequestBroadcast(5000)
step4 = ReceiveRespondAcks()
step5 = ReceiveRespondResponseHeaders(validate_header)
step6 = ReceiveResponseContents(on_reponse_received)

step1.set_next(step2)
step2.set_next(step3)
step3.set_next(step4)
step4.set_next(step5)
step5.set_next(step6)

while True:
	process = RequestProcess()
	process.request_content = raw_input("enter request: ")
	step1.handle(process)