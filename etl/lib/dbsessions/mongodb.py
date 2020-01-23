# -*- coding: utf-8 -*-
import json
from pandas import DataFrame
import re
from tg.i18n import ugettext as _
from tg.exceptions import HTTPPreconditionFailed


class MongoDBSession(object):
    _session = None
    _collection = None

    def __init__(self, url):
        collection = None
        if u'#' in url:
            url, collection = url.rsplit('#', 1)
        self.set_session(url)
        if collection is not None:
            self.set_collection(collection)

    def set_session(self, url):
        from pymongo import MongoClient
        self._session = MongoClient(url)

    def set_collection(self, collection):
        self._collection = self._session.get_default_database() \
            .get_collection(collection)

    def extract_directive_value(self, query, directive_pattern):
        pattern = r'^[\s]*#' + re.escape(directive_pattern) + r'.*' + re.escape('=') + r'.*'
        directive_match = re.search(pattern, query)
        if directive_match:
            value = directive_match.group(0).split('=')[-1].strip()
            return value, directive_match
        elif not directive_match and self._collection is not None:
            return None, None
        else:
            raise HTTPPreconditionFailed(
                detail=
                'Missing collection, it should be something like "#collection=collectionname" in the query or'
                'specify the url in form mongodb://user:pass@host:port/database#collection'
            )

    def parse_q(self, q):
        collection_name, sub_re = self.extract_directive_value(q, 'collection')
        if collection_name is not None and sub_re is not None:
            if collection_name not in self._session.get_default_database().list_collection_names():
                raise HTTPPreconditionFailed(
                    detail='The requested collection: %s doesn\'t exist, check it' % collection_name
                )
            query = re.sub(sub_re.group(0), '', q)
            self.set_collection(collection_name)
        else:
            query = q
        try:
            query = json.loads(query)
        except (TypeError, ValueError) as ex:
            raise HTTPPreconditionFailed('Wrong query format, query must be valid json')
        return query

    def execute(self, q):
        query = self.parse_q(q)
        if isinstance(query, dict):
            data = self._collection.find(query)
        elif isinstance(query, list):
            data = self._collection.aggregate(query)
        return DataFrame(list(data))

    def rollback(self):
        pass                # pragma no cover
