#!/home/zanfranceschi/Projects/request-broadcast-protocol/src/python/virtenv/bin/python
# -*- coding: utf-8 -*-

import pprint
from rbprotocol_client import RBProcolClient
import common
import json

pp = pprint.PrettyPrinter(indent=4)


def search_callback(result):
	pp.pprint(result.body)
	print "-" * 100


def all_received(results):
	i = sum([len(r.body) for r in results])
	print "total of {} results".format(i)

def validate_header(header):
	return True


client = RBProcolClient(
	"localhost",
	5000,
	10,
	100,
	10,
	search_callback,
	all_received)

while True:
	search = raw_input("enter request: ")
	request = common.Request("application/json", "utf-8", search)
	client.request(request)