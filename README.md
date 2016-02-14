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
