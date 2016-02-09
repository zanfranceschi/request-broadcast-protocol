using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ZeroMQ;
using System.Xml.Schema;

namespace DistributedSearch.Root
{
	class Program
	{
		static void Main(string[] args)
		{
			using (ZContext context = new ZContext())
			using (ZSocket searchRequest = new ZSocket(context, ZSocketType.PUB))
			using (ZSocket searchReplyAck = new ZSocket(context, ZSocketType.ROUTER))
			using (ZSocket searchReply = new ZSocket(context, ZSocketType.ROUTER))
			{
				searchRequest.Bind("tcp://*:5000");
				searchReplyAck.Bind("tcp://*:5001");
				searchReply.Bind("tcp://*:5002");

				while (true)
				{
					Console.WriteLine("enter your search term:");
					string q = Console.ReadLine();

					Console.WriteLine("enter the categories you'd like to search (comma separeted):");
					string[] categories = Console.ReadLine().Split(','); //new string[] { "*" };

					Search search = new Search
					{
						Q = q,
						Categories = categories
					};

					string searchId = Guid.NewGuid().ToString();

					Console.WriteLine("ID: {0}", searchId);

					using (ZMessage message = new ZMessage(new List<ZFrame>()
						{ 
							new ZFrame("search_notification"),          // topic
							new ZFrame(searchId),                       // search ID
							new ZFrame("tcp://localhost:5001"), 		// reply ack endpoint 
							new ZFrame("tcp://localhost:5002"),   		// reply endpoint
							new ZFrame("UTF-8"),						// encoding
							new ZFrame(search.Serialize())                  // search object
						}))
					{
						searchRequest.Send(message);

						IList<ZMessage> acks = new List<ZMessage>();

						ZError error;

						ZPollItem poll = ZPollItem.CreateReceiver();

						Console.WriteLine("waiting acks...");

						// get acks
						while (true)
						{
							ZMessage msg;

							// We wait acks for certain time only.
							// If no (more) acks are received for 100ms inside this while loop, we go to the next step
							// Slow working nodes responding previous searches might be a problem here since no TTL exists in 0MQ
							if (searchReplyAck.PollIn(poll, out msg, out error, TimeSpan.FromMilliseconds(100)))
							{
								string ackSearchId = msg[1].ReadString(); // Second frame is search id. 

								// This prevents results from previous searches to be included, usually caused by slow working nodes.
								if (ackSearchId == searchId)
									acks.Add(msg);
							}
							else if (error == ZError.EAGAIN)
							{
								break;
							}
						}

						Console.WriteLine("{0} acks received", acks.Count);

						IList<ZMessage> results = new List<ZMessage>();

						Console.WriteLine("waiting results...");

						// Get results if there are any
						while (results.Count < acks.Count)
						{
							ZMessage msg;

							// Since results are probably larger, we wait longer
							if (searchReply.PollIn(poll, out msg, out error, TimeSpan.FromSeconds(15)))
							{
								string replySearchId = msg[1].ReadString(); // Second frame is search id -- again

								// Again, this prevents results from previous searches to be included
								if (replySearchId == searchId)
								{
									results.Add(msg);
									string node = msg[2].ReadString();
									Console.WriteLine("result received from {0}", node);
									Console.WriteLine("{0}%", Math.Round(((float)results.Count / (float)acks.Count) * 100f));
								}
							}
							else if (error == ZError.EAGAIN)
							{
								break;
							}
						}

						Console.WriteLine("{0} nodes responded", results.Count);

						IList<SearchResult> searchResults = new List<SearchResult>();

						foreach (ZMessage result in results)
						{
							#region bug in the zeromq wrapper
							//string nodeId = result[1].ReadString();
							string payload = "";
							string tmpPayload = "";
							do
							{
								tmpPayload = result[3].ReadString();
								payload += tmpPayload;
							}
							while (!string.IsNullOrEmpty(tmpPayload));
							#endregion

							SearchResult searchResult = payload.Deserialize<SearchResult>();
							searchResults.Add(searchResult);
							Console.WriteLine(searchResult.SearchNode);
						}

						foreach (var searchResult in searchResults)
						{
							Console.WriteLine("node {0} has {1} results", searchResult.SearchNode, searchResult.ResultItems != null ? searchResult.ResultItems.Length : 0);
						}

						foreach (var searchResult in searchResults)
						{
							if (searchResult.ResultItems != null && searchResult.ResultItems.Length > 0)
							{
								foreach (var result in searchResult.ResultItems)
								{
									Console.WriteLine(
										"{0} - {1} @ {2}",
										result.Category,
										result.Description,
										result.Location);
								}
							}
						}
					}
				}
			}
		}
	}
}