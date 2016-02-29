#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import json
from rbprotocol.messages import Response
from rbprotocol.server import RequestResponder, Server
import requests
from settings import CLIENT_HOST


class PostsSearch(RequestResponder):
	def __init__(self, server_id):
		super(PostsSearch, self).__init__(server_id)
		r = requests.get("http://jsonplaceholder.typicode.com/posts/")
		self.posts = json.loads(r.text)

	def respond(self, request):
		q = request.body.lower().strip()
		result = [{
			"description": post["title"],
			"category": "post",
			"location": "http://jsonplaceholder.typicode.com/posts/"
		} for post in self.posts if q in post["title"].lower()]
		response = Response(
			request.header["correlation_id"],
			self.server_id,
			"application/json;utf-8",
			json.dumps(result))
		return response


server_id = "posts search"
search = PostsSearch(server_id)
server = Server(server_id, CLIENT_HOST, 5000, 1000, search)
print server_id, "accepting requests"
server.start()

