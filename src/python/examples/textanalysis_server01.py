#!/home/zanfranceschi/Projects/request-broadcast-protocol/src/python/virtenv/bin/python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
from rbprotocol.messages import Response
from rbprotocol.server import RequestResponder, Server
import re
from itertools import groupby


class AlphaAnalysis(RequestResponder):
	def __init__(self, server_id):
		super(AlphaAnalysis, self).__init__(server_id)

	def respond(self, request):
		q = request.body.upper().strip()
		matches = re.findall('[A-Z]+', q)
		query = ''.join([str(m) for m in matches])
		chars = [k for k, v in groupby(sorted(query))]

		with open('storage/text.txt') as f:
			text = f.read().replace('\n', '')

		result = ""
		result += "+-------+-------------+\n"
		result += "|  CHAR | OCCURRENCES |\n"
		result += "+-------+-------------+\n"

		for char in chars:
			result += "|   {}   |     {}    |\n".format(char, str(text.count(char)).rjust(4, '0'))

		result += "+-------+-------------+"

		response = Response(
			request.header["correlation_id"],
			self.server_id,
			"text/plain;utf-8",
			result)
		return response

server_id = "alpha chars analysis"
processor = AlphaAnalysis(server_id)
server = Server(server_id, "localhost", 4000, 1000, processor)
print server_id, "accepting requests"
server.start()
