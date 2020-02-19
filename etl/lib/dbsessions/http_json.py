# -*- coding: utf-8 -*-
import requests
from pandas import DataFrame


class HTTPJSONSession(object):
    def __init__(self, url):
        self._url = url.replace('json://', 'http://')

    def execute(self, q, limit=None):
        r = requests.get(self._url)
        content_type = r.headers['content-type']
        if 'json' not in r.headers['content-type']:
            raise ValueError("The content is presented as '{}' "
                             "while 'application/json' was expected".format(content_type))

        return DataFrame(r.json())

    def rollback(self):
        pass
