# -*- coding: utf-8 -*-
import json
from pandas import DataFrame
import re


class MongoDBSession(object):

    def __init__(self, url):
        from pymongo import MongoClient
        self._session = MongoClient(url)
        self._collection = None

    def set_collection(self, collection):
        self._collection = self._session.get_default_database()\
            .get_collection(collection)

    def extract_directive_value(self, query, directive_pattern):
        pattern = r'^#' + re.escape(directive_pattern) + r'.*'
        directive_match = re.search(pattern, query)
        value = directive_match.group(0).split('=')[-1].strip()
        return value, directive_match

    def parse_q(self, q):
        collection_name, sub_re = self.extract_directive_value(q, 'collection')
        self.set_collection(collection_name)
        return re.sub(sub_re.group(0), '', q)

    def execute(self, q):
        query = json.loads(self.parse_q(q))
        if isinstance(query, dict):
            data = self._collection.find(query)
        elif isinstance(query, list):
            data = self._collection.aggregate(query)
        return DataFrame(list(data))

    def rollback(self):
        pass
