#!/home/zanfranceschi/Projects/request-broadcast-protocol/src/python/virtenv/bin/python
# -*- coding: utf-8 -*-

from client import Client

client = Client("localhost", "tcp://*:5000", 5, 5000, 5000)

def validate_header(header):
	return True

def message_received_callback(flow, response):
	print response

while (True):
	q = raw_input("search term: ")
	client.request({ "q" : q }, validate_header, message_received_callback)