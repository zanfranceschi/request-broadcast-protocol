#!/home/zanfranceschi/Projects/request-broadcast-protocol/src/python/virtenv/bin/python
# -*- coding: utf-8 -*-

import abc
import zmq
from common import *


class ResponseDialogFlow(object):
	def __init__(self):
		self.request = None
		self.response = None
		self.response_header_invitation = None
		self.response_invitation = None


class ServerResponseStep(object):
	__metaclass__ = abc.ABCMeta

	def __init__(self, server_id):
		self.next = None
		self.server_id = server_id

	def set_next(self, step):
		self.next = step

	@abc.abstractmethod
	def handle(self, dialog_flow):
		pass


class Accept(ServerResponseStep):
	def __init__(self, server_id, hostname, port):
		super(Accept, self).__init__(server_id)
		self.context = zmq.Context.instance()
		self.socket = self.context.socket(zmq.SUB)
		self.socket.setsockopt(zmq.SUBSCRIBE, b'')
		self.socket.connect("tcp://{}:{}".format(hostname, port))

	def handle(self, dialog_flow):
		print "Accepting..."
		request_message = self.socket.recv_multipart()
		dialog_flow.request = Request.from_wire(request_message[0])
		if (self.next): self.next.handle(dialog_flow)


class SendAckReceiveResponseHeaderInvitation(ServerResponseStep):
	def __init__(self, server_id):
		super(SendAckReceiveResponseHeaderInvitation, self).__init__(server_id)
		self.context = zmq.Context.instance()
		self.socket = self.context.socket(zmq.DEALER)

	def handle(self, dialog_flow):
		self.socket.connect(dialog_flow.request.header["ack_endpoint"])
		self.socket.send(Ack(dialog_flow.request, self.server_id).to_wire())
		dialog_flow.response_header_invitation = ResponseHeaderInvitation.from_wire(self.socket.recv())
		self.socket.disconnect(self.socket.LAST_ENDPOINT)
		if (self.next): self.next.handle(dialog_flow)


class Search(ServerResponseStep):
	def __init__(self, server_id):
		super(Search, self).__init__(server_id)

	def handle(self, dialog_flow):
		q = dialog_flow.request.body.lower().strip()
		with open("db.txt") as f:
			lines = f.readlines()
			result = [{ 
				"description" : line.strip(),
				"category" : "fileContent",
				"location" : "db.txt@localhot"
				} for line in lines if q in line.lower().strip()]
		dialog_flow.response = Response(
			dialog_flow.request.header["correlation_id"],
			self.server_id,
			"application/json;utf-8",
			result)
		if (self.next): self.next.handle(dialog_flow)


class SendResponseHeaderReceiveResponseInvitation(ServerResponseStep):
	def __init__(self, server_id):
		super(SendResponseHeaderReceiveResponseInvitation, self).__init__(server_id)
		self.context = zmq.Context.instance()
		self.socket = self.context.socket(zmq.DEALER)

	def handle(self, dialog_flow):
		self.socket.connect(dialog_flow.response_header_invitation.header["response_header_endpoint"])
		self.socket.send(ResponseHeader(dialog_flow.response).to_wire())
		dialog_flow.response_invitation = ResponseInvitation.from_wire(self.socket.recv())
		self.socket.disconnect(self.socket.LAST_ENDPOINT)
		if (self.next): self.next.handle(dialog_flow)


class TrySendResponseContent(ServerResponseStep):
	def __init__(self, server_id):
		super(TrySendResponseContent, self).__init__(server_id)
		self.context = zmq.Context.instance()
		self.socket = self.context.socket(zmq.DEALER)

	def handle(self, dialog_flow):
		if (dialog_flow.response_invitation.header["status"] == 100):
			self.socket.connect(dialog_flow.response_invitation.header["response_endpoint"])
			self.socket.send(dialog_flow.response.to_wire())
			self.socket.disconnect(self.socket.LAST_ENDPOINT)
			print dialog_flow.response.to_wire()
		if (self.next): self.next.handle(dialog_flow)


server_id = "teste"

step1 = Accept(server_id, "localhost", 5000)
step2 = SendAckReceiveResponseHeaderInvitation(server_id)
step3 = Search(server_id)
step4 = SendResponseHeaderReceiveResponseInvitation(server_id)
step5 = TrySendResponseContent(server_id)

step1.set_next(step2)
step2.set_next(step3)
step3.set_next(step4)
step4.set_next(step5)
step5.set_next(step1)

dialog_flow = ResponseDialogFlow()
step1.handle(dialog_flow)
