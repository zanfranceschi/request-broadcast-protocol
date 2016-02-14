package org.distributedsearch.node;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;

import org.zeromq.ZMQ;
import org.zeromq.ZMQ.Context;
import org.zeromq.ZMQ.Socket;

import com.google.gson.Gson;

public class FileSystemNode {

	public static void main(String[] args) throws IOException {

		Properties props = new Properties();
		props.load(new FileInputStream("config.properties"));

		Context context = ZMQ.context(1);
		Socket subSocket = context.socket(ZMQ.SUB);
		subSocket.connect(props.getProperty("sub_endpoint"));
		subSocket.subscribe(props.getProperty("sub_prefix").getBytes());

		Socket ackSocket = context.socket(ZMQ.DEALER);
		Socket replySocket = context.socket(ZMQ.DEALER);

		String id = props.getProperty("node_id");
		String location = props.getProperty("location");
		String searchPath = props.getProperty("search_path");

		while (!Thread.currentThread().isInterrupted()) {

			System.out.println("listening...");

			subSocket.recvStr(); // topic

			String searchId = subSocket.recvStr();
			String ackEndpoint = subSocket.recvStr();

			ackSocket.connect(ackEndpoint);
			ackSocket.sendMore(searchId);
			ackSocket.send(id);

			System.out.println("acked");

			String replyEndpoint = subSocket.recvStr();
			String encoding = subSocket.recvStr();
			String payload = subSocket.recvStr();

			System.out.println(payload);

			Gson gson = new Gson();
			
			Search search = gson.fromJson(payload, Search.class);

			SearchResult searchResult = new SearchResult();
			searchResult.search = search;
			searchResult.searchNode = id;
			List<ResultItem> results = new ArrayList<ResultItem>();

			Files.walk(Paths.get(searchPath)).forEach(path -> {
				if (path.toString().toLowerCase().contains(search.q.toLowerCase())) {

					ResultItem item = new ResultItem();

					if (path.toFile().isDirectory()) {
						item.category = "directory";
					} else {
						item.category = "file";
					}

					item.description = path.toFile().getName();
					item.location = path.toString() + "@" + location;
					results.add(item);
				}
			});

			ResultItem[] resultItems = new ResultItem[results.size()];
			resultItems = results.toArray(resultItems);
			searchResult.resultItems = resultItems;

			String serializedSearchResult = gson.toJson(searchResult);

			replySocket.connect(replyEndpoint);

			replySocket.sendMore(searchId);
			replySocket.sendMore(id);
			replySocket.send(serializedSearchResult);
			System.out.println("replied:");
			System.out.println(serializedSearchResult);
			System.out.println("------------------------");
		}

		subSocket.close();
		context.term();
		System.out.println("bye");
	}
}
