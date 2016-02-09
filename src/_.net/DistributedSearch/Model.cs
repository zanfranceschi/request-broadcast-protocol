using Newtonsoft.Json;

namespace DistributedSearch
{
	[JsonObject]
	public class Search
	{
		[JsonProperty("categories")]
		public string[] Categories { get; set; }

		[JsonProperty("q")]
		public string Q { get; set; }
	}

	[JsonObject]
	public class SearchResult
	{
		[JsonProperty("search")]
		public Search Search { get; set; }

		[JsonProperty("searchNode")]
		public string SearchNode { get; set; }

		[JsonProperty("resultItems")]
		public ResultItem[] ResultItems { get; set; }
	}

	[JsonObject]
	public class ResultItem
	{
		[JsonProperty("description")]
		public string Description { get; set; }

		[JsonProperty("category")]
		public string Category { get; set; }

		[JsonProperty("location")]
		public string Location { get; set; }
	}

	public static class ExtensionMethods
	{
		public static string Serialize<T>(this T obj)
			where T : new()
		{
			return JsonConvert.SerializeObject(obj);
		}

		public static T Deserialize<T>(this string obj)
			where T : new()
		{
			return JsonConvert.DeserializeObject<T>(obj);
		}
	}
}