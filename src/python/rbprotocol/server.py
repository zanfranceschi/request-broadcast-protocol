# -*- coding: utf-8 -*-

import abc
import zmq
from messages import *


class RequestResponder(object):
	__metaclass__ = abc.ABCMeta

	def __init__(self, server_id):
		self.server_id = server_id

	@abc.abstractmethod
	def respond(self, request):
		return


class ResponseDialogFlow(object):
	def __init__(self):
		self.request = None
		self.response = None
		self.response_header_invitation = None
		self.response_invitation = None
		self.timed_out = False


class ServerResponseStep(object):
	__metaclass__ = abc.ABCMeta

	def __init__(self, server_id):
		self.next = None
		self.server_id = server_id

	def set_next(self, step):
		self.next = step
		return step

	@abc.abstractmethod
	def handle(self, dialog_flow):
		pass


class WaitingServerResponseStep(ServerResponseStep):
	__metaclass__ = abc.ABCMeta

	def __init__(self, server_id, timeout):
		super(WaitingServerResponseStep, self).__init__(server_id)
		self.timeout = timeout


class Accept(ServerResponseStep):
	def __init__(self, server_id, hostname, port):
		super(Accept, self).__init__(server_id)
		self.context = zmq.Context.instance()
		self.socket = self.context.socket(zmq.SUB)
		self.socket.setsockopt(zmq.SUBSCRIBE, b'')
		self.socket.connect("tcp://{}:{}".format(hostname, port))

	def handle(self, dialog_flow):
		dialog_flow = ResponseDialogFlow()
		request_message = self.socket.recv_multipart()
		dialog_flow.request = Request.from_wire(request_message[0])
		if (self.next):
			self.next.handle(dialog_flow)


class SendAckReceiveResponseHeaderInvitation(WaitingServerResponseStep):
	def __init__(self, server_id, timeout):
		super(SendAckReceiveResponseHeaderInvitation, self).__init__(server_id, timeout)
		self.context = zmq.Context.instance()
		self.socket = self.context.socket(zmq.DEALER)

	def handle(self, dialog_flow):
		if (not dialog_flow.timed_out):
			self.socket.connect(dialog_flow.request.header["ack_endpoint"])
			self.socket.send(Ack(dialog_flow.request, self.server_id).to_wire())
			if (self.socket.poll(self.timeout)):
				dialog_flow.response_header_invitation = ResponseHeaderInvitation.from_wire(self.socket.recv())
			else:
				dialog_flow.timed_out = True
			self.socket.disconnect(self.socket.LAST_ENDPOINT)
		if (self.next):
			self.next.handle(dialog_flow)


class CreateResponse(ServerResponseStep):
	def __init__(self, server_id, request_responder):
		super(CreateResponse, self).__init__(server_id)
		self.request_responder = request_responder

	def handle(self, dialog_flow):
		if (not dialog_flow.timed_out):
			dialog_flow.response = self.request_responder.respond(dialog_flow.request)
		if (self.next):
			self.next.handle(dialog_flow)


class SendResponseHeaderReceiveResponseInvitation(WaitingServerResponseStep):
	def __init__(self, server_id, timeout):
		super(SendResponseHeaderReceiveResponseInvitation, self).__init__(server_id, timeout)
		self.context = zmq.Context.instance()
		self.socket = self.context.socket(zmq.DEALER)

	def handle(self, dialog_flow):
		if (not dialog_flow.timed_out):
			self.socket.connect(dialog_flow.response_header_invitation.header["response_header_endpoint"])
			self.socket.send(ResponseHeader(dialog_flow.response).to_wire())
			if (self.socket.poll(self.timeout)):
				dialog_flow.response_invitation = ResponseInvitation.from_wire(self.socket.recv())
			else:
				dialog_flow.timed_out = True
			self.socket.disconnect(self.socket.LAST_ENDPOINT)
		if (self.next):
			self.next.handle(dialog_flow)


class TrySendResponseContent(ServerResponseStep):
	def __init__(self, server_id):
		super(TrySendResponseContent, self).__init__(server_id)
		self.context = zmq.Context.instance()
		self.socket = self.context.socket(zmq.DEALER)

	def handle(self, dialog_flow):
		if (not dialog_flow.timed_out and dialog_flow.response_invitation.header["status"] == 100):
			self.socket.connect(dialog_flow.response_invitation.header["response_endpoint"])
			self.socket.send(dialog_flow.response.to_wire())
			self.socket.disconnect(self.socket.LAST_ENDPOINT)
		if (self.next):
			self.next.handle(dialog_flow)


class Server(object):
	def __init__(self, server_id, connect_to_host, connect_to_port, client_timeout, request_responder):
		self.server_id = server_id
		self.accept = Accept(server_id, connect_to_host, connect_to_port)
		handle_acks = SendAckReceiveResponseHeaderInvitation(server_id, client_timeout)
		create_response = CreateResponse(server_id, request_responder)
		send_header = SendResponseHeaderReceiveResponseInvitation(server_id, client_timeout)
		try_send_response = TrySendResponseContent(server_id)

		self.accept.set_next(handle_acks)\
			.set_next(create_response)\
			.set_next(send_header)\
			.set_next(try_send_response)\
			.set_next(self.accept)

	def start(self):
		self.accept.handle(None)
