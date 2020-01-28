# -*- coding: utf-8 -*-
"""Template Helpers used in etl."""
import logging
from markupsafe import Markup
from datetime import datetime
from bokeh.embed import components
from bokeh.resources import INLINE
from bokeh.palettes import Category10
import itertools

log = logging.getLogger(__name__)


def current_year():
    now = datetime.now()
    return now.strftime('%Y')


def icon(icon_name):
    return Markup('<i class="glyphicon glyphicon-%s"></i>' % icon_name)


def color_gen():
    for c in itertools.cycle(Category10[10]):
        yield c


def show_graph(graph):
    script, div = components(graph, INLINE)
    return Markup(div + '\n' + script)


def is_number(x):
    try:
        return isinstance(float(x), (float))
    except:
        return False


def is_boolean(x):
    try:
        return int(x) == 0 or int(x) == 1
    except:
        return False


def is_datetime(x):
    # parse('675') -> datetime.datetime(675, 1, 28, 0, 0)
    if is_number(x):
        return False
    from datetime import datetime
    from dateutil.parser import parse
    try:
        return True if isinstance(parse(x), datetime) else False
    except:
        return False


# PROVVISORIO, DA SOSTITUIRE CON REGEX IN FUTURO
def escape_string_to_js(s):
    s = {key:value.replace("\n", "\\n") for (key, value) in list(s.items())}
    s = {key:value.replace(""" "value != value" """, """ \\"value != value\\" """) for (key, value) in list(s.items())}
    s = {key:value.replace(""" "value == value" """, """ \\"value == value\\" """) for (key, value) in list(s.items())}
    return s


def dashboards():
    from etl.model import DBSession, Dashboard
    return DBSession.query(Dashboard).all()


row = '<div class="row">'
close_row = '</div>'

# Import commonly used helpers from WebHelpers2 and TG
from tg.util.html import script_json_encode
from tg.jsonify import encode
try:
    from webhelpers2 import date, html, number, misc, text
except SyntaxError:
    log.error("WebHelpers2 helpers not available with this Python Version")
