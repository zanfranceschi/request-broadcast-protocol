#!/home/zanfranceschi/Projects/request-broadcast-protocol/src/python/virtenv/bin/python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.abspath('..'))
from rbprotocol.messages import Request
from rbprotocol.client import Client


def search_callback(response):
	print ""
	print response.header["id"].upper()
	print response.body


client = Client('localhost', 4000, 10, 1000, 100, search_callback)

while True:
	content = raw_input("\nEnter alphanumeric content for text analysis: ")
	request = Request("text/plain", "utf-8", content)
	client.request(request)
