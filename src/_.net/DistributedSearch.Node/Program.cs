using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ZeroMQ;

namespace DistributedSearch.Node
{
	/// <summary>
	/// Helper class to abstract the "distributed search protocol".
	/// </summary>
	public abstract class Node
	{
		protected string _id;
		protected string _searchNotificationsEndpoint;
		protected string _topicPrefix;
		private bool _listen;

		protected Node(string id, string searchNotificationsEndpoint, string topicPrefix)
		{
			_id = id;
			_searchNotificationsEndpoint = searchNotificationsEndpoint;
			_topicPrefix = topicPrefix;
		}

		protected abstract bool CanHandleSearch(Search search);

		protected abstract SearchResult Search(Search search);

		public void Stop()
		{
			_listen = false;
		}

		public void Start()
		{
			_listen = true;
            
			using (ZContext context = new ZContext())
			using (ZSocket searchSubscription = new ZSocket(context, ZSocketType.SUB))
			using (ZSocket searchReplyAck = new ZSocket(context, ZSocketType.DEALER))
			using (ZSocket searchReply = new ZSocket(context, ZSocketType.DEALER))
			{
				searchSubscription.Connect(_searchNotificationsEndpoint);
				searchSubscription.Subscribe(_topicPrefix);

				while (_listen)
				{
					using (ZMessage searchRequest = searchSubscription.ReceiveMessage())
					{

						string charset = searchRequest[4].ReadString();

						#region bug in the zeromq wrapper
						string xml = "";
						string tpmXml = "";
						do
						{
							tpmXml = searchRequest[5].ReadString();
							xml += tpmXml;
						}
						while (!string.IsNullOrEmpty(tpmXml));
						#endregion
                        
						Search search = xml.Deserialize<Search>();
                        
						if (!CanHandleSearch(search))
						{
							continue;
						}

						string replyAckEndpoint = searchRequest[2].ReadString();
						string searchId = searchRequest[1].ReadString();
                        
						searchReplyAck.Connect(replyAckEndpoint);
                        
						using (ZMessage ack = new ZMessage(new List<ZFrame>
							{
								new ZFrame(searchId),
								new ZFrame(_id)
							}))
						{
							searchReplyAck.Send(ack);
						}

						string replyEndpoint = searchRequest[3].ReadString();

						searchReply.Connect(replyEndpoint);

						SearchResult result = Search(search);

						using (ZMessage reply = new ZMessage(new List<ZFrame>
							{
								new ZFrame(searchId),
								new ZFrame(_id),
								new ZFrame(result.Serialize<SearchResult>()),
							}))
						{
							searchReply.Send(reply);
						}
					}
				}
			}
		}
	}
}
