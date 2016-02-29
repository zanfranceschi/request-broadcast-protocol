#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import json
from rbprotocol.messages import Request
from rbprotocol.client import Client
from settings import CLIENT_HOST


def search_callback(response):
	results = json.loads(response.body)
	for result in results:
		print "{}: {}".format(response.header["id"], result["description"])


def all_received(responses):
	print "-" * 50
	for response in responses:
		print "{}: {} results".format(response.header["id"], len(json.loads(response.body)))
	print "-" * 50


client = Client(CLIENT_HOST, 5000, 100, 1000, 1000, search_callback, all_received)

while True:
	search = raw_input("enter your search term: ")
	request = Request("application/json", "utf-8", search)
	client.request(request)
