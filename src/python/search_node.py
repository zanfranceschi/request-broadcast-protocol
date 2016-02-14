#!/home/zanfranceschi/Projects/distributed-search/src/python/virtenv/bin/python
# -*- coding: utf-8 -*-

import json
import zmq

class Server(object):
	def __init__(self, request_endpoint):
		self.request_endpoint = request_endpoint
		ctx = zmq.Context()
		socket_sub = ctx.socket(zmq.SUB)
		socket_sub.connect(request_endpoint)
		socket_sub.setsockopt(zmq.SUBSCRIBE, b'')

		socket_ack = ctx.socket(zmq.DEALER)
		socket_header = ctx.socket(zmq.DEALER)
		socket_body = ctx.socket(zmq.DEALER)




ctx = zmq.Context()
socket_sub = ctx.socket(zmq.SUB)
socket_sub.connect("tcp://localhost:5000")
socket_sub.setsockopt(zmq.SUBSCRIBE, b'')

socket_ack = ctx.socket(zmq.DEALER)
socket_header = ctx.socket(zmq.DEALER)
socket_body = ctx.socket(zmq.DEALER)

node_id = "python"

try:
	while True:
		print "listening..."
		raw_request = socket_sub.recv()

		request = json.loads(raw_request)

		correlation_id = request["header"]["correlation_id"]

		# ack
		socket_ack.connect(request["header"]["ack_endpoint"])

		ack_request = {
			"correlation_id" : correlation_id,
			"id" : node_id
		}

		socket_ack.send(json.dumps(ack_request))
		ack_response = json.loads(socket_ack.recv())
		# /ack

		q = request["body"]["q"].lower().strip()

		with open("db.txt") as f:
			lines = f.readlines()
			result = [{ 
				"description" : line.strip(),
				"category" : "fileContent",
				"location" : "db.txt@localhot"
				} for line in lines if q in line.lower().strip()]

		response_body = {
			"result" : result
		}

		response_body_serialized = json.dumps(response_body)

		reply_header = {
			"correlation_id"	: correlation_id,
			"id"				: node_id,
			"content_length"	: len(response_body_serialized),
			"content_type"		: "application/json;utf-8",
		}
		socket_header.connect(ack_response["response_header_endpoint"])
		socket_header.send(json.dumps(reply_header))
		header_reponse = json.loads(socket_header.recv())
		
		print header_reponse
		
		reply = {
			"header" : {
				"correlation_id" : correlation_id,
				"id" : node_id
			},
			"body" : response_body
		}

		print header_reponse["response_body_endpoint"]

		socket_body.connect(header_reponse["response_body_endpoint"])
		socket_body.send(json.dumps(reply))

		socket_ack.disconnect(socket_ack.LAST_ENDPOINT)
		socket_header.disconnect(socket_header.LAST_ENDPOINT)
		socket_body.disconnect(socket_body.LAST_ENDPOINT)


except KeyboardInterrupt:
	socket_sub.close()
	socket_header.close()
	socket_body.close()
	ctx.term()
	print "bye"