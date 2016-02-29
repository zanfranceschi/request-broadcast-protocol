#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
from rbprotocol.messages import Response
from rbprotocol.server import RequestResponder, Server
import re
from itertools import groupby
from settings import CLIENT_HOST


class AlphaAnalysis(RequestResponder):
	def __init__(self, server_id):
		super(AlphaAnalysis, self).__init__(server_id)
		with open('storage/text.txt') as f:
			file_content = f.read().replace('\n', '')
		matches = re.findall('[A-Z]+', file_content)
		all_alphas = ''.join([str(m) for m in matches])
		alphas = [k.upper() for k, v in groupby(sorted(all_alphas))]
		self.occurrences = {alpha: str(file_content.count(alpha)).rjust(4, '0') for alpha in alphas}

	def respond(self, request):
		q = request.body.upper().strip()
		matches = re.findall('[A-Z]+', q)
		query = ''.join([str(m) for m in matches])
		chars = [k for k, v in groupby(sorted(query))]

		result = ""
		result += "+-------+-------------+\n"
		result += "|  CHAR | OCCURRENCES |\n"
		result += "+-------+-------------+\n"

		for char in chars:
			if (char in self.occurrences):
				result += "|   {}   |     {}    |\n".format(char, self.occurrences[char])

		result += "+-------+-------------+"

		response = Response(
			request.header["correlation_id"],
			self.server_id,
			"text/plain;utf-8",
			result)
		return response

server_id = "alpha chars analysis"
processor = AlphaAnalysis(server_id)
server = Server(server_id, CLIENT_HOST, 4000, 5000, processor)
print server_id, "accepting requests"
server.start()
