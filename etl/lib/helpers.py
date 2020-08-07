# -*- coding: utf-8 -*-
"""Template Helpers used in etl."""
import logging


from markupsafe import Markup
from datetime import datetime
from bokeh.embed import components
from bokeh.resources import INLINE
import itertools
import numpy as np
import pandas as pd
import tg
from tg import flash, render_template
from kajiki import FileLoader
from bokeh.plotting import figure
from bokeh.palettes import viridis, linear_palette, Category10
from bokeh.transform import cumsum
from math import pi
import os, sys

log = logging.getLogger(__name__)


def current_year():
    now = datetime.now()
    return now.strftime('%Y')


def icon(icon_name):
    return Markup('<i class="glyphicon glyphicon-%s"></i>' % icon_name)


def color_gen():
    for c in itertools.cycle(Category10[10]):
        yield c


def pie_color(length):
    # raindow = ['#52D726', '#FFEC00', '#FF7300', '#FF0000', '#007ED6', '#7CDDDD']
    small_normal = ['#346699', '#6799cb', '#76cddd', '#d2edf3', '#d1e7c5', '#70c066', '#369946', '#026666']
    if length <= 8:
        return linear_palette(small_normal, length)
    return viridis(length)


def pie_result(result, axis):
    if len(result) > 256:
        result_other = result[axis[1]][255:]
        result = result[:255]
        result = result.append({axis[0]: 'Others', axis[1]: result_other.sum()}, ignore_index=True)
    result['angle'] = result[axis[1]] / result[axis[1]].sum() * 2 * pi
    result['color'] = pie_color(len(result))
    if '_id' in result.columns:
        result['_id'] = result['_id'].astype(str)
    return result


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
from webhelpers2 import date, html, number, misc, text


def get_graph(result, axis, visualizations):
    from etl.controllers.extractions import LINECHART_SUPPORTED_INDEXES
    if 'histogram' in visualizations:
        x = result[axis[0]].values
        y = result[axis[1]].values
        legend = 0
        try:
            visualizations['histogram'] = figure(x_range=x, width=800, height=600)
            visualizations['histogram'].vbar(x=x, top=y, width=0.75,
                                             color='#77d6d5', legend=axis[legend])
            visualizations['histogram'].y_range.start = 0
            visualizations['histogram'].y_range.end = max(y if y.size > 0 else [0])
            visualizations['histogram'].xaxis.major_label_orientation = "vertical"
        except Exception as e:
            log.exception('failed histogram visualization setup with exception: %s' % e)
            del visualizations['histogram']

    if 'linechart' in visualizations:
        if not isinstance(result.index, tuple(LINECHART_SUPPORTED_INDEXES)):
            flash('LineChart graph is only supported for scalar indexes, currently {}'.format(
                type(result.index)
            ), 'warning')
            visualizations.pop('linechart')

        if 'linechart' in visualizations:
            # Check it is still available after checks.

            x = result[axis[0]].values
            try:
                visualizations['linechart'] = figure(x_range=x, width=800, height=600)
            except:
                visualizations['linechart'] = figure(width=800, height=600)
            if result[axis[0]].dtype.type == np.datetime64:
                visualizations['linechart'] = figure(width=800, height=600, x_axis_type='datetime')

            for i, c in zip(range(1, len(axis)), color_gen()):
                y = result[axis[i]].values
                try:
                    visualizations['linechart'] = figure(y_range=y, width=800, height=600)
                except:
                    pass
                visualizations['linechart'].line(x, y, color=c, legend="x={},y={}".format(axis[0], axis[i]))
                visualizations['linechart'].circle(x, y, color=c, size=7)

    if 'pie' in visualizations or 'table+pie' in visualizations:
        visualizations['pie'] = figure(plot_height=600, width=800, x_range=(-0.5, 1.0),
                                       toolbar_location=None, tools="hover", tooltips="@%s: @%s" % (axis[0], axis[1]))
        result = pie_result(result, axis)
        visualizations['pie'].wedge(x=0, y=1, radius=0.4, start_angle=cumsum('angle', include_zero=True),
                                    end_angle=cumsum('angle'), line_alpha=0,
                                    fill_color='color', legend=axis[0], source=result)
        del result['angle']  # delete because I don't want them in the table
        del result['color']
        visualizations['pie'].axis.axis_label = None
        visualizations['pie'].axis.visible = False
        visualizations['pie'].grid.grid_line_color = None

    return visualizations


class RactivePartials:
    @staticmethod
    def _render(template_name, template_engine=None, **template_vars):
        return render_template(template_vars, template_engine=template_engine, template_name=template_name)

    def _render_js(self, template_name, template_dir='editor', **template_vars):
        loader = FileLoader(
            path=os.path.join(os.path.dirname(__file__), '../templates', template_dir),
            force_mode='text',
        )
        template = loader.import_(template_name)
        data = template_vars
        data.update(dict(
            h=sys.modules[__name__],
            tg=tg,
        ))
        return template(data).render()

    def extraction_visualization(self, *args, **kwargs):
        return self._render('etl.templates.editor.extraction_visualization', *args, **kwargs)

    def datasets_editor(self, *args, **kwargs):
        return self._render('etl.templates.editor.datasets_editor', *args, **kwargs)

    def steps_editor(self, *args, **kwargs):
        # explicitly call unescape because of ractive {{> partial call
        return self._render('etl.templates.editor.steps_editor', *args, **kwargs).unescape()

    def datasets_script(self, *args, **kwargs):
        return self._render_js('datasets_editor.kajiki.js', *args, **kwargs)

    def steps_script(self, *args, **kwargs):
        return self._render_js('steps_editor.kajiki.js', *args, **kwargs)

    def extraction_visualization_script(self, *args, **kwargs):
        return self._render_js('extraction_visualization_script.kajiki.js', *args, **kwargs)

    def dashboard_edit_extractions_template(self, *args, **kwargs):
        return self._render('etl.templates.dashboard.extraction_template', *args, **kwargs)

    def dashboard_edit_extractions_script(self, **kwargs):
        return self._render_js('extraction.kajiki.js', template_dir='dashboard', **kwargs)


ractive = RactivePartials()
