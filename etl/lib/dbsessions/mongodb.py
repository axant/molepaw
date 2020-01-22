# -*- coding: utf-8 -*-
import json
from pandas import DataFrame
import re
from tg.i18n import ugettext as _
from tg.exceptions import HTTPPreconditionFailed


class MongoDBSession(object):

    def __init__(self, url):
        from pymongo import MongoClient
        self._session = MongoClient(url)
        self._collection = None

    def set_collection(self, collection):
        if collection in self._session.get_default_database().list_collection_names():
            self._collection = self._session.get_default_database() \
                .get_collection(collection)
        else:
            raise HTTPPreconditionFailed(
                detail='The requested collection: %s doesn\'t exist, check it' % collection
            )

    def extract_directive_value(self, query, directive_pattern):
        pattern = r'^#' + re.escape(directive_pattern) + r'.*'
        directive_match = re.search(pattern, query)
        if directive_match:
            value = directive_match.group(0).split('=')[-1].strip()
            return value, directive_match
        else:
            raise HTTPPreconditionFailed(
                detail=_('Wrong collection directive syntax, it should be something like "#collection=collectionname"')
            )

    def parse_q(self, q):
        collection_name, sub_re = self.extract_directive_value(q, 'collection')
        self.set_collection(collection_name)
        return re.sub(sub_re.group(0), '', q)

    def execute(self, q):
        try:
            query = json.loads(self.parse_q(q))
        except (TypeError, ValueError) as ex:
            raise HTTPPreconditionFailed(_('Wrong query format, query must be valid json'))
        if isinstance(query, dict):
            data = self._collection.find(query)
        elif isinstance(query, list):
            data = self._collection.aggregate(query)
        return DataFrame(list(data))

    def rollback(self):
        pass
