#!/home/zanfranceschi/Projects/request-broadcast-protocol/src/python/virtenv/bin/python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
from rbprotocol.messages import Response
from rbprotocol.server import RequestResponder, Server
import re
from itertools import groupby


class NumberAnalysis(RequestResponder):
	def __init__(self, server_id):
		super(NumberAnalysis, self).__init__(server_id)
		with open('storage/text.txt') as f:
			self.text = f.read().replace('\n', '')

	def respond(self, request):
		q = request.body.strip()
		matches = re.findall('[0-9]+', q)
		query = ''.join([str(m) for m in matches])
		numbers = [k for k, v in groupby(sorted(query))]

		result = ""
		result += "+-------+-------------+\n"
		result += "|  NUMB | OCCURRENCES |\n"
		result += "+-------+-------------+\n"

		for number in numbers:
			result += "|   {}   |     {}    |\n".format(number, str(self.text.count(number)).rjust(4, '0'))

		result += "+-------+-------------+"

		response = Response(
			request.header["correlation_id"],
			self.server_id,
			"text/plain;utf-8",
			result)
		return response

server_id = "number chars analysis"
processor = NumberAnalysis(server_id)
server = Server(server_id, "localhost", 4000, 1000, processor)
print server_id, "accepting requests"
server.start()
