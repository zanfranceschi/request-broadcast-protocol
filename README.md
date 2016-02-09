# distributed-search

Distributed-Search is a proposed architecture for distributed and collaborative search. It's plataform agnostic and aims to provide very loose coupling between search and client nodes. The source code in this repository is for illustrative purposes only to show how it should work.

This pseudo protocol is more of an experiment and has a long way to go before use in production environments (if only it achieves this readiness).

A rough and very high level of how this works is depicted below:
![alt tag](https://raw.githubusercontent.com/zanfranceschi/distributed-search/master/docs/imgs/distributed-search-behaviour.jpg)

## source code

As previously mentioned, the source of this repo is for illustrative purposes only. There are implementations in three languages to exhibit the agnostic nature of this pseudo protocol.

The following is a brief explanation of the source code.

### .NET
- **DistributedSearch**: class library shared among all projects -- contains the serialization model helper methods
- **DistributedSearch.Node**: class library shared among all search node projects -- abstracts the "protocol" and facilitates implementing searching nodes
- **DistributedSearch.Node.Wikipedia**: console application -- implements a search node example that perform searches on Wikipedia using its search api
- **DistributedSearch.Root**: console application -- implements the client node.

**dependencies:**
- ZeroMQ
- Newtonsoft.Json


### Java
- The Java code solely implements a search node that searches file and dir names (not content) for a given path. Since Java is not a known language to me, I'd have taken long to implement a client node.

**dependencies:**
- eclipselink-2.5.0.jar
- jeromq-0.3.4.jar

### Python
- **client_node.py:** implements the client node.
- **search_node.py:** implements a search node that reads a file (**db.txt**) and searches lines containing the search criterion.

**dependencies:**
- pyzmq
- uuid
