#!/home/zanfranceschi/Projects/distributed-search/src/python/virtenv/bin/python
# -*- coding: utf-8 -*-

import json
import zmq
import uuid

ctx = zmq.Context()
socket_pub = ctx.socket(zmq.PUB)
socket_ack = ctx.socket(zmq.ROUTER)
socket_reply = ctx.socket(zmq.ROUTER)

socket_pub.bind("tcp://*:5000")
socket_ack.bind("tcp://*:5001")
socket_reply.bind("tcp://*:5002")

try:
	while True:
		q = raw_input("enter your search term: ")
		categories = raw_input("enter the categories you'd like to search (comma separated): ").split(',')

		search = { "q" : q, "categories" : categories }

		search_id = str(uuid.uuid4())

		print "id:", search_id

		for i in range(20):
			socket_pub.send(b'bosta de array de bytes')

		socket_pub.send("search_notification", zmq.SNDMORE) 		# topic
		socket_pub.send(search_id, zmq.SNDMORE) 					# searchId
		socket_pub.send("tcp://localhost:5001", zmq.SNDMORE) 		# ack endpoint
		socket_pub.send("tcp://localhost:5002", zmq.SNDMORE) 		# reply endpoint
		socket_pub.send("UTF-8", zmq.SNDMORE) 						# reply endpoint
		socket_pub.send(json.dumps(search)) 						# search object

		acks = []

		while True:
			if socket_ack.poll(100, zmq.POLLIN):
				msg_ack = socket_ack.recv_multipart()
				acks.append(msg_ack)
			else:
				break

		print len(acks), "acks received"

		results = []

		print "waiting results..."

		while len(results) < len(acks):
			if socket_reply.poll(15 * 1000):
				reply_message = socket_reply.recv_multipart()
				reply_search_id = reply_message[1]

				if reply_search_id == search_id:
					results.append(reply_message)
			else:
				break
		
		print len(results), "nodes responded"

		search_results = [json.loads(result[3]) for result in results]

		for search_result in search_results:
			print "node", search_result["searchNode"], "has", len(search_result["resultItems"]), "results"

		for search_result in search_results:
			result_items = search_result["resultItems"]
			for result_item in result_items:
				print result_item
except KeyboardInterrupt:
	socket_pub.close()
	socket_ack.close()
	socket_reply.close()
	ctx.term()
	print "bye"