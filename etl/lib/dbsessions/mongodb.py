# -*- coding: utf-8 -*-
import json
from pandas import DataFrame


class MongoDBSession(object):
    def __init__(self, url):
        from pymongo import MongoClient

        try:
            url, collection = url.rsplit('#', 1)
        except ValueError:
            raise ValueError('url does not provide the collection name, splace specify url in form '
                             'mongodb://user:pass@host:port/database#collection')

        self._session = MongoClient(url)
        self._collection = self._session.get_default_database()[collection]

    def execute(self, q):
        q = json.loads(q)
        if isinstance(q, dict):
           data = self._collection.find(q)
        elif isinstance(q, list):
           data = self._collection.aggregate(q)
        return DataFrame(list(data))

    def rollback(self):
        pass
