# Request Broadcast Protocol

The Request Broadcast Protocol (RBP) is a high level protocol designed to work with clients and multiple servers whose existence is not known. 


## Motivation

I wanted to build a search engine capable of searching into different and unstructured metada such as objects database tables, application deployments, code repositories, etc. The main challenge of such search engine were more about how to design such disparate components to colaborate than implementing the individual components search. I found the architecture interesting enough to elaborate this high level protocol.


## High Level Flow

- Client broadcasts (publishes in a pub/sub fashion) a request with an ack random endpoint
- Servers receive the request notification and acks back to client
- For each received ack, client responds with a "send response header to" random endpoint (in a HTTP Expect: 100-continue header fashion)
- Servers receive the "send response header to" and send the response header to client containing information about the response body
- For each received response header, client checks it and responds with a "send response body to" (status 100) random endpoint if the response header is satisfactory, or responds with a 417 status (not satisfactory header response)
- Servers receive the "send response body to" and send the response body to client
- Finally, client receives response bodies from all available servers

```
+------------+ 								      	  +------------+
|  			 |        	broadcast request	 		  |            |
|			 | -------------------------------------> |			   |
|			 |                        				  |			   |
|			 |          		   ack          	  |			   |
|			 | <------------------------------------- |			   |
|			 |                        				  |			   |
|			 |    	 header response endpoint    	  |			   |
|			 | -------------------------------------> |			   |
|   CLIENT	 |                        				  | N SERVERS  |
|	    	 |    		  header response   		  |			   |
|			 | <------------------------------------- |			   |
|			 |                          	 		  |			   |
|			 |         continue | don't contiue   	  |			   |
|			 | -------------------------------------> |			   |
|			 |                        				  |			   |
|			 |      content response (if continue)    |			   |
|			 | <------------------------------------- |			   |
+------------+										  +------------+
```

## Protocol Status

The protocol as well as its implementation are still in very early stages.

## Usage Example

### A Distributed Search Engine - Oh!

The following example represents a very simple distributed search engine with two search nodes. One search node searches lines of a text file and the other searches on http://jsonplaceholder.typicode.com/posts/.

#### Client Node
```python
import json
from rbprotocol.messages import Request
from rbprotocol.client import Client


def search_callback(response):
	# create the response callback
	# for each response, this will be invoked
	results = json.loads(response.body)
	for result in results:
		print "{}: {}".format(response.header["id"], result["description"])

"""
The client node
Arguments are:
	- endpoint to broadcast requests
	- port to bind
	- ack timeout
	- header timeout
	- response timeout
	- response received callback
"""
client = Client("localhost", 5000, 10, 2500, 100, search_callback)

# start the client node
while True:
	search = raw_input("enter your search term: ")
	request = Request("application/json", "utf-8", search)
	client.request(request)
```

#### FileSearch Server Node
```python
import json
from rbprotocol.messages import Response
from rbprotocol.server import RequestResponder, Server


class FileSearch(RequestResponder):
	def __init__(self, server_id):
		super(FileSearch, self).__init__(server_id)

	def respond(self, request):
		q = request.body.lower().strip()
		with open("db.txt") as f:
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


# instantiate and start the server
server_id = "db.txt search"
search = FileSearch(server_id)
"""
Arguments are:
	- the server identification
	- the endpoint requests will be broadcast
	- port of the requests broadcast endpoint
	- time to wait in ms for the client node to reply during the protocol dialog
	- the object that understands requests and transforms them into responses (the thing that matters)
"""
server = Server(server_id, "localhost", 5000, 1000, search)
server.start()
```

#### PostsSearch Server Node
```python
import json
from rbprotocol.messages import Response
from rbprotocol.server import RequestResponder, Server
import requests


class PostsSearch(RequestResponder):
	def __init__(self, server_id):
		super(PostsSearch, self).__init__(server_id)

	def respond(self, request):
		r = requests.get("http://jsonplaceholder.typicode.com/posts/")
		posts = json.loads(r.text)
		q = request.body.lower().strip()
		result = [{
			"description" : post["title"],
			"category" : "post",
			"location" : "http://jsonplaceholder.typicode.com/posts/"
		} for post in posts if q in post["title"].lower()]
		response = Response(
			request.header["correlation_id"],
			self.server_id,
			"application/json;utf-8",
			json.dumps(result))
		return response
		
# instantiate and start the server
server_id = "posts search"
search = PostsSearch(server_id)
server = Server(server_id, "localhost", 5000, 1000, search)
server.start()
```

If you run the three parts, you'll have the client broadcasting requests and receiving responses from two "strange" servers.

If you have a question, comment, or anything else, please leave me a note at zanfranceschi[@]gmail.com -- I'll be glad to reply.
