#!/home/zanfranceschi/Projects/request-broadcast-protocol/src/python/virtenv/bin/python
# -*- coding: utf-8 -*-
"""
The module is an example of how to use servers and clients
for the RB Protocol.

Usage:
	- make this file executable
	- replace the first line of this file with Python executable of you OS (I use virtenv, that's why the long path here)
	- to run the servers, execute ./usage_example.py server
	- to run the client, execute ./usage_example.py client
	- fiddle with the example
"""
import sys
import os
sys.path.insert(0, os.path.abspath('..'))


def server_example():
	"""
	Very simple servers usage examples.

	Here, we use two servers to demonstrate the
	collaborative nature of the Request Broadcast Protocol
	"""
	import json
	from rbprotocol.messages import Response
	from rbprotocol.server import RequestResponder, Server
	import requests
	import thread

	class FileSearch(RequestResponder):
		def __init__(self, server_id):
			super(FileSearch, self).__init__(server_id)

		def respond(self, request):
			q = request.body.lower().strip()
			with open("storage/db.txt") as f:
				lines = f.readlines()
				result = [{
					"description" : line.strip(),
					"category" : "fileContent",
					"location" : "db.txt"
					} for line in lines if q in line.lower().strip()]
			response = Response(
				request.header["correlation_id"],
				self.server_id,
				"application/json;utf-8",
				json.dumps(result))
			return response

	class PostsSearch(RequestResponder):
		def __init__(self, server_id):
			super(PostsSearch, self).__init__(server_id)
			r = requests.get("http://jsonplaceholder.typicode.com/posts/")
			self.posts = json.loads(r.text)

		def respond(self, request):
			q = request.body.lower().strip()
			result = [{
				"description" : post["title"],
				"category" : "post",
				"location" : "http://jsonplaceholder.typicode.com/posts/"
			} for post in self.posts if q in post["title"].lower()]
			response = Response(
				request.header["correlation_id"],
				self.server_id,
				"application/json;utf-8",
				json.dumps(result))
			return response

	def db_txt_search():
		server_id = "db.txt search"
		search = FileSearch(server_id)
		server = Server(server_id, "localhost", 5000, 1000, search)
		server.start()

	def posts_search():
		server_id = "posts search"
		search = PostsSearch(server_id)
		server = Server(server_id, "localhost", 5000, 1000, search)
		server.start()

	thread.start_new(db_txt_search, ())
	thread.start_new(posts_search, ())
	print "servers accepting requests..."
	raw_input("press any key to quit...")


def client_example():
	"""
	Very simple client usage example
	"""
	import json
	from rbprotocol.messages import Request
	from rbprotocol.client import Client

	def search_callback(response):
		results = json.loads(response.body)
		for result in results:
			print "{}: {}".format(response.header["id"], result["description"])

	def all_received(responses):
		print "-" * 50
		for response in responses:
			print "{}: {} results".format(response.header["id"], len(json.loads(response.body)))
		print "-" * 50

	client = Client('localhost', 5000, 10, 1000, 100, search_callback, all_received)

	while True:
		search = raw_input("enter your search term: ")
		request = Request("application/json", "utf-8", search)
		client.request(request)


if __name__ == "__main__":
	import sys
	if (sys.argv[1] == "server"):
		server_example()

	if (sys.argv[1] == "client"):
		client_example()
