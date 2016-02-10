# Distributed-Search

Distributed-Search is a proposed architecture for distributed and collaborative search. It's plataform agnostic and aims to provide very loose coupling between search and client nodes. The source code in this repository is for illustrative purposes only to show how it should work.

This high level protocol is more of an experiment and has a long way to go before being production ready (if only it achieves this readiness).

A rough and high level of how this works is depicted below:
![alt tag](https://raw.githubusercontent.com/zanfranceschi/distributed-search/master/docs/imgs/distributed-search-behaviour.jpg)

This search architecture is composed by two kinds of nodes or components:
- **Client Node:** The component responsible for transmitting the search notification to search nodes in an indirect way (using the pub/sub messaging pattern).
- **Search Node:** The component that receives search notifications; checks if it can perform the search; if it can, it then _acks_ to the Client Node; and then sends the search results.

## Source Code

As previously mentioned, the source of this repo is for illustrative purposes only. There are implementations in three languages to exhibit the agnostic nature of this pseudo protocol.

The following is a brief explanation of the source code.

### .NET
- **DistributedSearch**: Class library shared among all projects -- contains the serialization model and helper methods.
- **DistributedSearch.Node**: Class library shared among all search node projects -- abstracts the "protocol" and facilitates implementing searching nodes.
- **DistributedSearch.Node.Wikipedia**: Console application -- implements a search node example that perform searches on Wikipedia using its search api
- **DistributedSearch.Root**: Console application -- implements the client node.

**dependencies:**
- ZeroMQ
- Newtonsoft.Json

### Java
- The Java code solely implements a search node that searches file and dir names (not content) for a given path. It's in my TODO list to implement the Java client node.

**dependencies:**
- eclipselink-2.5.0.jar
- jeromq-0.3.4.jar

### Python
- **client_node.py:** Implements the client node.
- **search_node.py:** Implements a search node that reads a file (**db.txt**) and searches lines containing the search criterion.

**dependencies:**
- pyzmq
- uuid

## Backlog

**TODO**
- A more detailed explanation of the protocol.
- Java Client Node implementation.
- Parallel Client Nodes implementation.
- Results relevance ordering.

**ISSUES**
- If a Search Node sends a very large result set, it may clog up the Client Node very badly.
- Slow Search Nodes increases Client Node check times for acks and results. The use of a messaging system that implements message TTL -- like RabbitMQ, for example -- could sort this out. I'd rather come up with an idea to still use ZeroMQ -- it's blazing fast and I really like the brokerless nature of it.

