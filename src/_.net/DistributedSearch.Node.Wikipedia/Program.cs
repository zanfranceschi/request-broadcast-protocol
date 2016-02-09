using System;
using System.Xml;
using System.Configuration;
using System.Net;
using System.IO;
using System.Xml.Serialization;
using System.Linq;
using System.Net.Sockets;
using System.Collections.Generic;

namespace DistributedSearch.Node.Wikipedia
{
	class MainClass
	{
		public static void Main(string[] args)
		{
			WikipediaNode node = new WikipediaNode();
			node.Start();
		}
	}

	public class WikipediaNode
		: Node
	{
		public WikipediaNode()
			: base(
				ConfigurationManager.AppSettings["node-id"],
				ConfigurationManager.AppSettings["notifications-endpoint"],
				ConfigurationManager.AppSettings["notifications-prefix"])
		{
		}

		protected override bool CanHandleSearch(Search search)
		{
			return true;
		}

		protected override SearchResult Search(Search search)
		{
			HttpWebRequest request = (HttpWebRequest)HttpWebRequest.Create(string.Format("https://en.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch={0}&format=xml&gsrprop=snippet&prop=info&inprop=url", search.Q));
			request.Method = "GET";
			WebResponse response = request.GetResponse();
			var stream = response.GetResponseStream();
			StreamReader reader = new StreamReader(stream);

			string xml = reader.ReadToEnd();

			Console.WriteLine(xml);

			XmlSerializer serializer = new XmlSerializer(typeof(api));
			StringReader stringReader = new StringReader(xml);

			api api = (api)serializer.Deserialize(stringReader);

			ResultItem[] resultItems = null;

			if (
				api.query != null
				&& api.query.pages != null
				&& api.query.pages.Any())
			{
				resultItems = (
				    from p in api.query.pages
				    select new ResultItem
				{
					Category = "url",
					Description = p.title,
					Location = p.fullurl
				}).ToArray();
			}

			return new SearchResult
			{ 
				Search = search, 
				ResultItems = resultItems, 
				SearchNode = "wikipedia"
			};
		}
	}

	[XmlRootAttribute]
	public class api
	{
		[XmlElement]
		public query query { get; set; }
	}

	[XmlRootAttribute]
	public class query
	{
		[XmlArrayItem("page")]
		[XmlArray("pages")]
		public page[] pages { get; set; }
	}

	[XmlRootAttribute]
	public class page
	{
		[XmlAttribute]
		public string title { get; set; }

		[XmlAttribute]
		public string fullurl { get; set; }
	}
}
