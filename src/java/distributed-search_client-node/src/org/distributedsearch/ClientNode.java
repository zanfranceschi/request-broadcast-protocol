package org.distributedsearch;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.UUID;

import org.zeromq.ZFrame;
import org.zeromq.ZLoop;
import org.zeromq.ZMQ;
import org.zeromq.ZMQ.Context;
import org.zeromq.ZMQ.PollItem;
import org.zeromq.ZMQ.Poller;
import org.zeromq.ZMQ.Socket;
import org.zeromq.ZMsg;

import com.google.gson.Gson;

public class ClientNode {

	public static void main(String[] args) throws IOException {

		Context context = ZMQ.context(1);
		Socket pubSocket = context.socket(ZMQ.PUB);
		Socket ackSocket = context.socket(ZMQ.ROUTER);
		Socket replySocket = context.socket(ZMQ.ROUTER);

		pubSocket.bind("tcp://*:5000");
		ackSocket.bind("tcp://*:5001");
		replySocket.bind("tcp://*:5002");

		ackSocket.setReceiveTimeOut(20);
		replySocket.setReceiveTimeOut(5 * 1000);

		while (!Thread.currentThread().isInterrupted()) {

			BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
			System.out.print("enter your search term:");
			String q = br.readLine();

			System.out.print("enter the categories you'd like to search (comma separated):");
			String[] categories = br.readLine().split(",");

			Search search = new Search();
			search.q = q;
			search.categories = categories;

			Gson gson = new Gson();

			String searchId = UUID.randomUUID().toString();

			System.out.println("search id: " + searchId);

			pubSocket.send("search_notification", ZMQ.SNDMORE);
			pubSocket.send(searchId, ZMQ.SNDMORE);
			pubSocket.send("tcp://localhost:5001", ZMQ.SNDMORE);
			pubSocket.send("tcp://localhost:5002", ZMQ.SNDMORE);
			pubSocket.send("UTF-8", ZMQ.SNDMORE);
			pubSocket.send(gson.toJson(search));

			ArrayList<ZMsg> acks = new ArrayList<>();

			Poller poller = new Poller(1);
			
			poller.register(ackSocket, Poller.POLLIN);

			while (true) {
			
				System.out.println(poller.poll(20));
				
				if (poller.pollin(0)) {
					System.out.println("-----------------------");
					String ackSearchId = ackSocket.recvStr();
					String nodeId = ackSocket.recvStr();

					System.out.println(ackSearchId);
					System.out.println(nodeId);
					System.out.println("-----------------------");
				} else {
					break;
				}
			}
		}
	}
}
