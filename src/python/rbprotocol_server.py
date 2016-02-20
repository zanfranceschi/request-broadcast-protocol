#!/home/zanfranceschi/Projects/request-broadcast-protocol/src/python/virtenv/bin/python
# -*- coding: utf-8 -*-

import abc
import zmq
import json

class ResponseProcess(object):
	def __init__(self):
		self.correlation_id = None
		self.request_header = None
		self.request_content = None
		self.ack_header = None
		self.response_header = None
		self.response_response_header = None
		self.response = None


class ServerResponseStep(object):
	__metaclass__ = abc.ABCMeta

	def __init__(self):
		self.next = None

	def set_next(self, step):
		self.next = step

	@abc.abstractmethod
	def handle(self, response_process):
		pass


class Accept(ServerResponseStep):
	def __init__(self, hostname, port):
		super(Accept, self).__init__()
		self.context = zmq.Context.instance()
		self.socket = self.context.socket(zmq.SUB)
		self.socket.setsockopt(zmq.SUBSCRIBE, b'')
		self.socket.connect("tcp://{}:{}".format(hostname, port))

	def handle(self, response_process):
		print "Accepting..."
		raw_request = self.socket.recv_multipart()
		response_process.request_header = json.loads(raw_request[0])
		response_process.request_content = raw_request[1]
		response_process.correlation_id = response_process.request_header["correlation_id"]
		if (self.next): self.next.handle(response_process)


class SendReceiveAck(ServerResponseStep):
	def __init__(self, server_id):
		super(SendReceiveAck, self).__init__()
		self.server_id = server_id
		self.context = zmq.Context.instance()
		self.socket = self.context.socket(zmq.DEALER)

	def handle(self, response_process):
		ack_request = json.dumps({
			"correlation_id" : response_process.correlation_id,
			"id" : self.server_id
		})
		self.socket.connect(response_process.request_header["ack_endpoint"])
		self.socket.send(ack_request)
		response_process.ack_header = json.loads(self.socket.recv())
		self.socket.disconnect(self.socket.LAST_ENDPOINT)
		if (self.next): self.next.handle(response_process)


class Search(ServerResponseStep):
	def __init__(self, server_id):
		super(Search, self).__init__()

	def handle(self, response_process):
		q = response_process.request_content.lower().strip()
		with open("db.txt") as f:
			lines = f.readlines()
			result = [{ 
				"description" : line.strip(),
				"category" : "fileContent",
				"location" : "db.txt@localhot"
				} for line in lines if q in line.lower().strip()]
		response_process.response_content = json.dumps(result)
		if (self.next): self.next.handle(response_process)


class SendReceiveResponseHeader(ServerResponseStep):
	def __init__(self, server_id):
		super(SendReceiveResponseHeader, self).__init__()
		self.server_id = server_id
		self.context = zmq.Context.instance()
		self.socket = self.context.socket(zmq.DEALER)

	def handle(self, response_process):
		response_process.response_header = json.dumps({
			"correlation_id"	: response_process.correlation_id,
			"id"				: self.server_id,
			"content_length"	: len(response_process.response_content),
			"content_type"		: "application/shit;utf-8"
		})
		self.socket.connect(response_process.ack_header["response_header_endpoint"])
		self.socket.send(response_process.response_header)
		response_process.response_response_header = json.loads(self.socket.recv())
		self.socket.disconnect(self.socket.LAST_ENDPOINT)
		if (self.next): self.next.handle(response_process)


class TrySendResponseContent(ServerResponseStep):
	def __init__(self):
		super(TrySendResponseContent, self).__init__()
		self.server_id = server_id
		self.context = zmq.Context.instance()
		self.socket = self.context.socket(zmq.DEALER)

	def handle(self, response_process):
		if ("response_content_endpoint" in response_process.response_response_header):
			self.socket.connect(response_process.response_response_header["response_content_endpoint"])
			self.socket.send_multipart([response_process.response_header, response_process.response_content])
			self.socket.disconnect(self.socket.LAST_ENDPOINT)
		if (self.next): self.next.handle(response_process)


server_id = "teste"

step1 = Accept("localhost", 5000)
step2 = SendReceiveAck(server_id)
step3 = Search(server_id)
step4 = SendReceiveResponseHeader(server_id)
step5 = TrySendResponseContent()

step1.set_next(step2)
step2.set_next(step3)
step3.set_next(step4)
step4.set_next(step5)
step5.set_next(step1)

while True:
	step1.handle(ResponseProcess())