# -*- coding: utf-8 -*-
try:
    import StringIO
except ImportError:
    import io as StringIO
import csv
from six import ensure_str
import sys
import json
from tg import config
from tg.predicates import Predicate
import traceback

try:
    unicode('test Python2')
except Exception:
    unicode = str

try:
    from sys import exc_traceback
except ImportError as i:
    pass  # not needed on py3

py_version = sys.version_info[:2][0]

def dateframe_to_csv(dataframe):
    csvfile = StringIO.StringIO()
    writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow(['INDEX'] + list(dataframe.columns))
    for row in dataframe.itertuples():
        writer.writerow([v.encode('utf-8') if isinstance(v, unicode) and py_version < 3 else v for v in row])
    return csvfile.getvalue()


def dateframe_to_json(dataframe):
    converted_data = json.loads(dataframe.to_json(orient='records', date_format='iso'))

    data = []
    for idx, row in enumerate(dataframe.itertuples()):
        d = dict(INDEX=row[0])
        d.update(converted_data[idx])
        data.append(d)
    return json.dumps(data)


def stringfy_exc(ex):
    try:  # py3
        return (
            '{}: {}'.format(type(ex).__name__, str(ex)),
            ''.join(traceback.format_exception(type(ex), ex, ex.__traceback__))
        )
    except AttributeError:  # py2
        return (
            '{}: {}'.format(type(ex).__name__, str(ex)),
            ''.join(traceback.format_exception(ex.__class__, ex, sys.exc_traceback))
        )

def force_text(v):
    try:
        return ensure_str(v)
    except Exception as ex:
        return str(v)


class is_api_authenticated(Predicate):
    """
    Check that the current user authenticated using the API Key
    """
    message = "Requires a valid API Token"

    def evaluate(self, environ, credentials):
        if 'datasource_api_token' not in config:
            self.unmet()

        if config['datasource_api_token'] not in environ['QUERY_STRING']:
            self.unmet()

