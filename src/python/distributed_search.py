#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import zmq

ctx = zmq.Context()
socket_sub = ctx.socket(zmq.SUB)
socket_sub.connect("tcp://localhost:5000")
socket_sub.setsockopt(zmq.SUBSCRIBE, "search_notification")

socket_ack = ctx.socket(zmq.DEALER)
socket_reply = ctx.socket(zmq.DEALER)

node_id = "python"

while True:
	print "listening..."
	msg = socket_sub.recv_multipart()

	search_id = msg[1]
	ack_endpint = msg[2]
	reply_endpint = msg[3]
	encoding = msg[4]
	payload = msg[5]

	socket_ack.connect(ack_endpint)
	socket_ack.send(search_id, zmq.SNDMORE)
	socket_ack.send(node_id)

	print "acked"

	print payload

	search = json.loads(payload)

	with open("db.txt") as f:
		lines = f.readlines()
		result_items = [{ 
			"description" : line.strip(),
			"category" : "fileContent",
			"location" : "db.txt@localhot"
			} for line in lines if search["q"].lower().strip() in line.lower().strip()]

	search_result = {
		"search" : search,
		"searchNode" : node_id,
		"resultItems" : result_items
	}

	socket_reply.connect(reply_endpint)
	socket_reply.send(search_id, zmq.SNDMORE)
	socket_reply.send(node_id, zmq.SNDMORE)
	socket_reply.send(json.dumps(search_result))

	print "replied:"
	print search_result
	print "-" * 50