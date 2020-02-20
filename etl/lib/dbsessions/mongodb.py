# -*- coding: utf-8 -*-
import json
from pandas import DataFrame
import re
from tg.i18n import ugettext as _
from pymongo import MongoClient


class MongoDBSession(object):
    _session = None
    default_collection = None  # the one specified in the connection url

    def __init__(self, url):
        collection = None
        if u'#' in url:
            url, collection = url.rsplit('#', 1)
        self.set_session(url)
        if collection is not None:
            self.default_collection = collection

    def set_session(self, url):
        self._session = MongoClient(url)

    def get_collection(self, collection):
        if collection in self._session.get_default_database().list_collection_names():
            return self._session.get_default_database().get_collection(collection)
        else:
            raise ValueError('collection {} does not exists'.format(collection))

    def parse_query(self, query):
        q_parts = []
        directives = {}
        for line in query.split('\n'):
            stripped_line = line.strip()
            if stripped_line[:1] == "#":
                key, value = [v.strip() for v in stripped_line.split("=", 1)]
                directives[key.strip('#').strip()] = value
            else:
                q_parts.append(line)
        q = json.loads('\n'.join(q_parts).strip())
        return q, directives

    def execute(self, q, limit=None):
        query, directives = self.parse_query(q)
        if 'collection' in directives.keys():
            collection = self.get_collection(directives['collection'])
        elif self.default_collection is not None:
            collection = self.get_collection(self.default_collection)
        else:
            raise ValueError('no collection specified')
        if isinstance(query, dict):
            data = collection.find(query)
            if limit is not None:
                data = data.limit(limit)
        elif isinstance(query, list):
            query_limit = [d for d in query if '$limit' in d.keys()]
            if len(query_limit) == 1 and limit is not None:
                query_limit = query_limit[0]
                query_limit['$limit'] = limit
            elif limit is not None:
                query.append({u'$limit': limit})

            data = collection.aggregate(query)
        return DataFrame(list(data))

    def rollback(self):
        pass                # pragma no cover
