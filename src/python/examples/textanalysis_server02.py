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


class NumberAnalysis(RequestResponder):
	def __init__(self, server_id):
		super(NumberAnalysis, self).__init__(server_id)
		with open('storage/text.txt') as f:
			file_content = f.read().replace('\n', '')
		matches = re.findall('[0-9]+', file_content)
		all_nums = ''.join([str(m) for m in matches])
		nums = [k for k, v in groupby(sorted(all_nums))]
		self.occurrences = {num: str(file_content.count(num)).rjust(4, '0') for num in nums}

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
			if (number in self.occurrences):
				result += "|   {}   |     {}    |\n".format(number, self.occurrences[number])

		result += "+-------+-------------+"

		response = Response(
			request.header["correlation_id"],
			self.server_id,
			"text/plain;utf-8",
			result)
		return response

server_id = "number chars analysis"
processor = NumberAnalysis(server_id)
server = Server(server_id, CLIENT_HOST, 4000, 1000, processor)
print server_id, "accepting requests"
server.start()
