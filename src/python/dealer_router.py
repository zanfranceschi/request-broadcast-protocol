#!/home/zanfranceschi/Projects/distributed-search/src/python/virtenv/bin/python
# -*- coding: utf-8 -*-

import zmq
import time
import sys

def router():
	ctx = zmq.Context()
	router = ctx.socket(zmq.ROUTER)
	router2 = ctx.socket(zmq.ROUTER)
	router.bind("tcp://*:5000")
	router2.bind("tcp://*:5001")
	try:
		while True:
			print "listening..."
			req = router.recv_multipart()
			print req
			router.send_multipart([req[0], "tcp://localhost:5001"])

			req2 = router2.recv_multipart()
			print req2

	except KeyboardInterrupt:
		router.close()
		ctx.term()

def dealer():
	ctx = zmq.Context()
	dealer = ctx.socket(zmq.DEALER)
	dealer2 = ctx.socket(zmq.DEALER)
	dealer.connect("tcp://localhost:5000")
	print "starting to send"
	try:
		while True:
			dealer.send("hello")
			reply = dealer.recv()
			dealer2.connect(reply)
			dealer2.send("hello2")
			print reply
			time.sleep(1)
	except KeyboardInterrupt:
		dealer.close()
		ctx.term()


func = sys.argv[1]

if func == "router":
	print "router..."
	router()
else:
	print "dealer..."
	dealer()