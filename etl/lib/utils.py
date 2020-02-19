# -*- coding: utf-8 -*-
try:
    import StringIO
except ImportError:
    import io as StringIO
import csv
from six import ensure_str
import sys
import json
import tg
from tg.predicates import Predicate
import traceback

try:
    unicode('test Python2')
except Exception:
    unicode = str

# try:
#    from sys import exc_traceback
# except ImportError as i:
#     from sys import exc_info as exc_traceback

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
    return ''.join(traceback.format_exception(type(ex), ex, ex.__traceback__))


def force_text(v):
    try:
        return ensure_str(v)
    except Exception as ex:
        return str(v)

# def force_text(v):
#     if isinstance(v, str):
#         return unicode(v, 'utf-8').encode('ascii', 'replace')
#     elif isinstance(v, unicode):
#         return v.encode('ascii', 'replace')
#     else:
#         return unicode(v).encode('ascii', 'replace')


class is_api_authenticated(Predicate):
    """
    Check that the current user authenticated using the API Key
    """
    message = "Requires a valid API Token"

    def evaluate(self, environ, credentials):
        if 'datasource_api_token' not in tg.config:
            self.unmet()

        if tg.config['datasource_api_token'] not in environ['QUERY_STRING']:
            self.unmet()

