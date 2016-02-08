package org.distributedsearch.node;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;

import javax.xml.bind.JAXBException;

import org.eclipse.persistence.jaxb.JAXBContextProperties;
import org.eclipse.persistence.oxm.MediaType;
import javax.xml.bind.JAXBContext;
import javax.xml.bind.Unmarshaller;
import javax.xml.bind.Marshaller;
import javax.xml.transform.stream.StreamSource;
import java.io.StringReader;

import org.zeromq.ZMQ;
import org.zeromq.ZMQ.Context;
import org.zeromq.ZMQ.Socket;

public class FileSystemNode {

	public static void main(String[] args) throws IOException, JAXBException {

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

			JAXBContext ctx = JAXBContext.newInstance(Search.class, SearchResult.class, ResultItem.class);
			Unmarshaller unmarshaller = ctx.createUnmarshaller();
			unmarshaller.setProperty(JAXBContextProperties.MEDIA_TYPE, MediaType.APPLICATION_JSON);
			unmarshaller.setProperty(JAXBContextProperties.JSON_INCLUDE_ROOT, false);

			StringReader reader = new StringReader(payload);

			Search search = unmarshaller.unmarshal(new StreamSource(reader), Search.class).getValue();

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

			ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
			Marshaller marshaller = ctx.createMarshaller();
			marshaller.setProperty(JAXBContextProperties.MEDIA_TYPE, MediaType.APPLICATION_JSON);
			marshaller.setProperty(JAXBContextProperties.JSON_INCLUDE_ROOT, false);
			marshaller.marshal(searchResult, outputStream);

			replySocket.connect(replyEndpoint);

			replySocket.sendMore(searchId);
			replySocket.sendMore(id);
			replySocket.send(outputStream.toString());
			System.out.println("replied:");
			System.out.println(outputStream.toString(encoding));
			System.out.println("------------------------");
		}

		subSocket.close();
		context.term();
		System.out.println("bye");
	}
}
