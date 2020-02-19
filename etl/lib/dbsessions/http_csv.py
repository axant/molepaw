# -*- coding: utf-8 -*-
import csv
import requests
import tempfile
from pandas import DataFrame


class HTTPCSVSession(object):
    def __init__(self, url):
        self._url = url.replace('csv://', 'http://')

    def execute(self, q):
        r = requests.get(self._url)
        content_type = r.headers['content-type']
        if 'csv' not in r.headers['content-type']:
            raise ValueError("The content is presented as '{}' "
                             "while 'text/csv' was expected".format(content_type))

        with tempfile.SpooledTemporaryFile(mode='w') as csvfile:
            csvfile.write(r.content)
            csvfile.seek(0)
            csvdata = csv.reader(csvfile)

            headers = next(csvdata)
            df = DataFrame(list(csvdata))
            df.columns = headers
            return df

    def rollback(self):
        pass
