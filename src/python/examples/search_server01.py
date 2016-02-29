#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import json
from rbprotocol.messages import Response
from rbprotocol.server import RequestResponder, Server
from settings import CLIENT_HOST


class FileSearch(RequestResponder):
	def __init__(self, server_id):
		super(FileSearch, self).__init__(server_id)

	def respond(self, request):
		q = request.body.lower().strip()
		with open("storage/db.txt") as f:
			lines = f.readlines()
			result = [{
				"description": line.strip(),
				"category": "fileContent",
				"location": "db.txt"
				} for line in lines if q in line.lower().strip()]
		response = Response(
			request.header["correlation_id"],
			self.server_id,
			"application/json;utf-8",
			json.dumps(result))
		return response

server_id = "db.txt search"
search = FileSearch(server_id)
server = Server(server_id, CLIENT_HOST, 5000, 1000, search)
print server_id, "accepting requests"
server.start()
