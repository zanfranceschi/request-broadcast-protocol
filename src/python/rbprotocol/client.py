# -*- coding: utf-8 -*-

import abc
import zmq
from messages import *


def is_valid_response(response, request):
	return request.header["correlation_id"] == response.header["correlation_id"]


def validate_header_default(response, request):
	valid = response.header["correlation_id"] == request.header["correlation_id"]\
			and request.header["accept"].lower() in response.header["content_type"].lower()\
			and request.header["accept_charset"].lower() in response.header["content_type"].lower()
	return valid


class RequestDialogFlow(object):
	def __init__(self, hostname, request):
		self.hostname = hostname

		# messages
		self.request = request
		self.response_header_invitation = ResponseHeaderInvitation(request)
		self.response_invitation_continue = ResponseInvitationContinue(request)
		self.response_invitation_dontcontinue = ResponseInvitationDontContinue(request)

		# sockets
		self.ack_socket = None
		self.response_header_socket = None
		self.response_socket = None

		# responses
		self.acks = []
		self.response_headers = []
		self.responses = []


class ClientRequestStep(object):
	__metaclass__ = abc.ABCMeta

	def __init__(self):
		self.next = None

	def set_next(self, step):
		self.next = step
		return step

	@abc.abstractmethod
	def handle(self, dialog_flow):
		pass


class SetDynamicEndpoints(ClientRequestStep):
	def __init__(self):
		super(SetDynamicEndpoints, self).__init__()
		self.context = zmq.Context.instance()
		self.ack_socket = self.context.socket(zmq.ROUTER)
		self.response_header_socket = self.context.socket(zmq.ROUTER)
		self.response_socket = self.context.socket(zmq.ROUTER)
		self.ack_endpoint = None
		self.response_header_endpoint = None
		self.response_endpoint = None

	def _prepare_for_new_request(self, message, endpoint_name, hostname, socket):
		if (socket.LAST_ENDPOINT):
			socket.unbind(socket.LAST_ENDPOINT)
		port = socket.bind_to_random_port("tcp://*")
		message.header[endpoint_name] = "tcp://{}:{}".format(hostname, port)

	def handle(self, dialog_flow):
		self._prepare_for_new_request(dialog_flow.request, "ack_endpoint", dialog_flow.hostname, self.ack_socket)
		self._prepare_for_new_request(dialog_flow.response_header_invitation, "response_header_endpoint", dialog_flow.hostname, self.response_header_socket)
		self._prepare_for_new_request(dialog_flow.response_invitation_continue, "response_endpoint", dialog_flow.hostname, self.response_socket)
		dialog_flow.ack_socket = self.ack_socket
		dialog_flow.response_header_socket = self.response_header_socket
		dialog_flow.response_socket = self.response_socket
		if (self.next):
			self.next.handle(dialog_flow)


class SetTimeouts(ClientRequestStep):
	def __init__(self, ack_timeout, response_header_timeout, response_timeout):
		super(SetTimeouts, self).__init__()
		self.ack_timeout = ack_timeout
		self.response_header_timeout = response_header_timeout
		self.response_timeout = response_timeout

	def handle(self, dialog_flow):
		dialog_flow.request.header["ack_timeout"] = self.ack_timeout
		dialog_flow.response_header_invitation.header["response_header_timeout"] = self.response_header_timeout
		dialog_flow.response_invitation_continue.header["response_timeout"] = self.response_timeout
		if (self.next):
			self.next.handle(dialog_flow)


class RequestBroadcast(ClientRequestStep):
	def __init__(self, port):
		super(RequestBroadcast, self).__init__()
		self.context = zmq.Context.instance()
		self.request_socket = self.context.socket(zmq.PUB)
		self.request_socket.bind("tcp://*:{}".format(port))

	def handle(self, dialog_flow):
		self.request_socket.send(dialog_flow.request.to_wire())
		if (self.next): self.next.handle(dialog_flow)


class ReceiveRespondAcks(ClientRequestStep):
	def __init__(self):
		super(ReceiveRespondAcks, self).__init__()

	def handle(self, dialog_flow):
		while (True):
			if (dialog_flow.ack_socket.poll(dialog_flow.request.header["ack_timeout"])):
				responder_message = dialog_flow.ack_socket.recv_multipart()
				responder_id = responder_message[0]
				ack = Ack.from_wire(responder_message[1])
				if (ack.header["correlation_id"] == dialog_flow.request.header["correlation_id"]):
					dialog_flow.acks.append(ack)
					dialog_flow.ack_socket.send_multipart(
						[responder_id, dialog_flow.response_header_invitation.to_wire()])
			else:
				break
		if (self.next):
			self.next.handle(dialog_flow)


class ReceiveRespondResponseHeaders(ClientRequestStep):
	def __init__(self, validate_header):
		super(ReceiveRespondResponseHeaders, self).__init__()
		if (validate_header is None): validate_header = validate_header_default
		self.validate_header = validate_header

	def handle(self, dialog_flow):
		while (len(dialog_flow.response_headers) < len(dialog_flow.acks)):
			if (dialog_flow.response_header_socket.poll(dialog_flow.response_header_invitation.header["response_header_timeout"])):
				responder_msg = dialog_flow.response_header_socket.recv_multipart()
				responder_id = responder_msg[0]
				header = ResponseHeader.from_wire(responder_msg[1])
				if (self.validate_header(header, dialog_flow.request)):
					dialog_flow.response_headers.append(header)
					response = dialog_flow.response_invitation_continue
				else:
					response = dialog_flow.response_invitation_dontcontinue
				dialog_flow.response_header_socket.send_multipart([responder_id, response.to_wire()])
			else:
				break
		if (self.next):
			self.next.handle(dialog_flow)


class ReceiveResponses(ClientRequestStep):
	def __init__(self, on_response_received, on_all_responses_received):
		super(ReceiveResponses, self).__init__()
		self.on_response_received = on_response_received
		self.on_all_responses_received = on_all_responses_received

	def handle(self, dialog_flow):
		while (len(dialog_flow.responses) < len(dialog_flow.response_headers)):
			if (dialog_flow.response_socket.poll(dialog_flow.response_invitation_continue.header["response_timeout"])):
				responder_msg = dialog_flow.response_socket.recv_multipart()
				response = Response.from_wire(responder_msg[1])
				if (response.header["correlation_id"] == dialog_flow.request.header["correlation_id"]):
					dialog_flow.responses.append(response)
					if (self.on_response_received):
						self.on_response_received(response)
			else:
				break
		if (self.on_all_responses_received):
			self.on_all_responses_received(dialog_flow.responses)
		if (self.next):
			self.next.handle(dialog_flow)


class Client(object):
	def __init__(self,
				search_endpoint_hostname,
				search_endpoint_port,
				ack_timeout,
				response_header_timeout,
				response_timeout,
				on_reponse_received,
				on_all_responses_received=None,
				validate_header=None):

		self.hostname = search_endpoint_hostname
		self.set_dynamic_eps = SetDynamicEndpoints()
		set_timeouts = SetTimeouts(ack_timeout, response_header_timeout, response_timeout)
		request_broadcast = RequestBroadcast(search_endpoint_port)
		handle_acks = ReceiveRespondAcks()
		handle_response_headers = ReceiveRespondResponseHeaders(validate_header)
		handle_response_content = ReceiveResponses(on_reponse_received, on_all_responses_received)

		self.set_dynamic_eps.set_next(set_timeouts)\
			.set_next(request_broadcast)\
			.set_next(handle_acks)\
			.set_next(handle_response_headers)\
			.set_next(handle_response_content)\


	def request(self, request):
		dialog_flow = RequestDialogFlow(self.hostname, request)
		self.set_dynamic_eps.handle(dialog_flow)
