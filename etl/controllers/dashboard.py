from __future__ import division
from etl.lib.base import BaseController
from etl.lib.validators import validate_axis_against_extraction_visualization
from etl.model import Dashboard, DBSession, Extraction, DashboardExtractionAssociation
from tg import expose, flash, require,  lurl, validate,\
    request, redirect, predicates, abort
from tg.i18n import lazy_ugettext as l_
import tw2.forms as twf
import tw2.core as twc
import axf.bootstrap
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import func 
import logging
import numpy as np
from math import pi
import pandas
import pandas.tseries
from bokeh.plotting import figure
from bokeh.palettes import Category20
from bokeh.transform import cumsum
from etl.lib.helpers import color_gen, pie_result, gridify
import sys
import logging


log = logging.getLogger(__name__)


try:
    unicode('test Python2')
except Exception:
    unicode = str


log = logging.getLogger(__name__)
visualizationtypes = ('histogram', 'line', 'pie', 'sum', 'average')


LINECHART_SUPPORTED_INDEXES = (
    pandas.Index,
    pandas.DatetimeIndex,
    pandas.Int64Index,
    pandas.Float64Index,
)



class DashboardChangeName(twf.Form):
    inline_engine_name = 'genshi'
    template = '''
<form xmlns:py="http://genshi.edgewall.org/" py:attrs="w.attrs">
     <span class="error" py:content="w.error_msg"/>
     <div py:if="w.help_msg" class="help">
      <p>
         ${w.help_msg}
      </p>
     </div>
    ${w.child.display()}
</form>
    '''
    class child(axf.bootstrap.BootstrapFormLayout):
        inline_engine_name = 'genshi'
        template = '''
<div xmlns:py="http://genshi.edgewall.org/" py:strip="True">
    <py:for each="c in w.children_hidden">
        ${c.display()}
    </py:for>
    <div>
        <span id="${w.compound_id}:error" class="error" >
            <p py:for="error in w.rollup_errors" class="alert alert-danger">
               <span class="glyphicon glyphicon-exclamation-sign"></span>
               ${error}
           </p>
        </span>
    </div>
    <div class="form-horizontal">
        <div py:for="c in w.children_non_hidden"
             class="form-group ${((c.validator and getattr(c.validator, 'required', getattr(c.validator, 'not_empty', False))) and ' required' or '') + (c.error_msg and ' has-error' or '')}">
            <label py:if="c.label != None" class="col-sm-3 control-label" for="${c.compound_id}">
               $c.label
            </label>
            <div class="col-sm-7">
                ${c.display()}
                <span id="${c.compound_id}:error" class="error help-block" py:content="c.error_msg"/>
            </div>
            <div>${w.submit.display()}</div>
        </div>
    </div>
</div>
        '''

        uid = twf.HiddenField()
        name = twf.TextField(label='Dashboard Name',
                             validator=twc.Validator(required=True))
        submit = twf.SubmitButton(value=l_('Save'), css_class='btn btn-default col-sm-2')
    action = lurl('/dashboard/save_name')


class DashboardController(BaseController):

    @expose('etl.templates.dashboard.index')
    @require(predicates.not_anonymous())
    def index(self, id=None):
        try:
            if not id:
                dashboard = DBSession.query(Dashboard).first()
            else:
                dashboard = DBSession.query(Dashboard).filter_by(uid=id).one()
            if not dashboard:
                raise NoResultFound()
        except NoResultFound:
            return abort(404, detail='dashboard not found')
        sorted_extractions = dashboard.extractions
        sorted_extractions.sort(key=lambda e: e.index)
        from random import randint
        for e in sorted_extractions:
            e.columns = randint(3, 6)
        columned_extractions = gridify(sorted_extractions, getter=lambda e: e.columns)
        return dict(dashboard=dashboard, columned_extractions=columned_extractions)

    @expose('etl.templates.dashboard.edit')
    @require(predicates.in_group('admin'))
    def new(self):
        dashboard = Dashboard()
        dashboard.name = 'New dashboard'
        DBSession.add(dashboard)
        all_extractions = DBSession.query(Extraction).all()
        return dict(
            dashboard=dashboard,
            form_dashboard_name=DashboardChangeName(),
            form_dashboard_name_values=dashboard,
            visualizationtypes=visualizationtypes,
            all_extractions=all_extractions,
        )
    
    @expose('etl.templates.dashboard.edit')
    @require(predicates.in_group('admin'))
    def edit(self, id=None):
        try:
            dashboard = DBSession.query(Dashboard).filter_by(uid=id).one()
        except NoResultFound:
            return abort(404, detail='dashboard not found')
        all_extractions = DBSession.query(Extraction).all()
        return dict(
            dashboard=dashboard,
            form_dashboard_name=DashboardChangeName(),
            form_dashboard_name_values=dashboard,
            visualizationtypes=visualizationtypes,
            all_extractions=all_extractions,
        )

    @expose()
    @require(predicates.in_group('admin'))
    def delete(self, dashboard_id):
        if dashboard_id == '1':
            return abort(400, detail='cannot delete the main dashboard')
        dashboard = DBSession.query(Dashboard).filter_by(uid=dashboard_id).one()
        DBSession.delete(dashboard)
        return redirect('/dashboard')
        
    @expose()
    @require(predicates.in_group('admin'))
    @validate(DashboardChangeName, error_handler=edit)
    def save_name(self, **kw):
        try:
            dashboard = DBSession.query(Dashboard).filter_by(uid=kw['uid']).one()
        except NoResultFound:
            return abort(404, detail='dashboard not found')
        dashboard.name = kw['name']
        return redirect('/dashboard/edit/%s' % kw['uid'])

    @expose('json')
    @require(predicates.in_group('admin'))
    def save_extraction(self, dashboard_id, **kw):
        axis = request.json['graph_axis']
        visualization_type = request.json['visualization']
        validate_axis_against_extraction_visualization(
            visualization_type,
            axis,
            DBSession.query(Extraction).get(int(request.json['extraction_id']))
        )
        try:
            de = DBSession.query(DashboardExtractionAssociation).filter(
                DashboardExtractionAssociation.uid == request.json['uid'],
            ).one()
        except (NoResultFound, KeyError):
            de = DashboardExtractionAssociation()
            de.dashboard_id = int(dashboard_id)
            de.extraction_id = request.json['extraction_id']
            DBSession.add(de)
        de.extraction_id = request.json['extraction_id']
        de.visualization = visualization_type
        de.graph_axis = axis
        de.index = request.json['index']
        return dict(
            de=de,
            dashboard=de.dashboard,
            extraction=de.extraction,
        )

    @expose('json')
    @require(predicates.in_group('admin'))
    def delete_extraction(self, dashboard_id):
        uid = request.json['uid']
        try:
            de = DBSession.query(DashboardExtractionAssociation).filter(
                DashboardExtractionAssociation.uid == uid,
            ).one()
            DBSession.delete(de)
        except NoResultFound:
            pass
        return dict()

    @expose('json')
    @require(predicates.in_group('admin'))
    def set_extraction_index(self, dashboard_id):
        uid = request.json['uid']
        new_index = request.json['index']
        if new_index < 0:
            return abort(400, detail='cannot raise first extraction')
        last_index = DBSession.query(func.max(DashboardExtractionAssociation.index))\
                              .filter_by(dashboard_id=dashboard_id).one()[0]
        if new_index > last_index:
            return abort(400, detail='cannot lower last extraction')
        try:
            de = DBSession.query(DashboardExtractionAssociation).filter(
                DashboardExtractionAssociation.uid == uid,
            ).one()
        except NoResultFound:
            return abort(404, detail='dashboard not found')
        old_index = de.index
        try:
            other_de = DBSession.query(DashboardExtractionAssociation).filter(
                DashboardExtractionAssociation.dashboard_id == dashboard_id,
                DashboardExtractionAssociation.index == new_index,
            ).one()
            other_de.index = old_index
        except NoResultFound:
            other_de = None
        de.index = new_index
        return dict(de=de, other_de=other_de)

    @expose('json')
    @require(predicates.in_group('admin'))
    def extractions(self, dashboard_id, **kw):
        try:
            dashboard = DBSession.query(Dashboard).filter_by(uid=dashboard_id).one()
        except NoResultFound:
            return abort(404, detail='dashboard not found')
        extractions = [de.extraction for de in dashboard.extractions]
        return dict(extractions=extractions, dashboard=dashboard)

    @expose('json')
    @require(predicates.in_group('admin'))
    def get_extraction(self, uid):
        try:
            extraction = DBSession.query(Extraction).filter_by(uid=uid).one()
        except NoResultFound:
            return abort(404, detail='extraction not found')
        return dict(extraction=extraction)

    @expose('etl.templates.dashboard.extraction_widget')
    @require(predicates.not_anonymous())
    def extraction_widget(self, dashboard_id, **kw):
        de = DBSession.query(DashboardExtractionAssociation).filter_by(uid=kw['uid']).one()
        extraction = de.extraction
        try:
            result = extraction.perform()
        except Exception as e:
            log.exception('Failed to Retrieve Data')
            flash('ERROR RETRIEVING DATA: %s' % e, 'error')
            return redirect('/error')

        visualization = None
        axis = []
        if de.graph_axis:
            axis = [x.strip() for x in de.graph_axis.split(',')]

        if 'histogram' == de.visualization:
            x = result[axis[0]].values
            y = result[axis[1]].values
            legend = 0
            try:
                visualization = figure(x_range=x, sizing_mode='scale_width', height=400)
                visualization.vbar(x=x, top=y, width=0.75, color='#77d6d5')
                visualization.y_range.start = 0
                visualization.y_range.end = max(y if y.size > 0 else [0])
                visualization.xaxis.major_label_orientation = "vertical"
                visualization.toolbar_location = None
            except Exception as e:
                # return abort(400, detail=str(e))
                return redirect('/error', params={'detail': str(e)})

        elif 'line' == de.visualization:
            if not isinstance(result.index, LINECHART_SUPPORTED_INDEXES):
                return dict(error='LineChart graph is only supported for scalar indexes, currently {}'.format(
                    type(result.index)
                ))

            x = result[axis[0]].values
            try:
                visualization = figure(x_range=x, sizing_mode='scale_width', height=400)
            except:
                visualization = figure(sizing_mode='scale_width', height=400)
            if result[axis[0]].dtype.type == np.datetime64:
                from datetime import datetime
                x = [datetime(year=date.year, month=date.month, day=date.day) for date in
                     pandas.to_datetime(result[axis[0]].values)]
                visualization = figure(sizing_mode='scale_width', height=400, x_axis_type='datetime')

            for i, c in zip(range(1, len(axis)), color_gen()):
                y = [j.encode('utf8') if isinstance(j, unicode) else j for j in result[axis[i]].values.tolist()]
                try:
                    visualization = figure(y_range=y, sizing_mode='scale_width', height=400)
                except:
                    pass
                visualization.line(x, y, color=c)
                visualization.circle(x, y, color=c, size=3)

            visualization.toolbar_location = None
            visualization.yaxis.axis_line_width = None
            visualization.xgrid.grid_line_color = None
            visualization.outline_line_color = None
            visualization.xaxis.axis_line_color = "#777777"
            visualization.axis.minor_tick_in = 0
            visualization.axis.minor_tick_out = 0
            visualization.axis.major_tick_in = 0

        elif 'pie' == de.visualization:
            visualization = figure(plot_height=400, sizing_mode='scale_width', x_range=(-0.5, 1.0),
                                   toolbar_location=None, tools="hover", tooltips="@%s: @%s" % (axis[0], axis[1]))
            result = pie_result(result, axis)
            visualization.wedge(x=0, y=1, radius=0.4, start_angle=cumsum('angle', include_zero=True),
                                end_angle=cumsum('angle'), line_alpha=0,
                                fill_color='color', legend=axis[0], source=result)
            visualization.axis.axis_label = None
            visualization.axis.visible = False
            visualization.grid.grid_line_color = None
            visualization.toolbar_location = None
            visualization.outline_line_color = None
            visualization.legend.border_line_alpha = 0
            visualization.legend.location = "center_right"
            visualization.legend.label_text_font_size = '9pt'
            visualization.legend.glyph_height = 18
            visualization.legend.glyph_width = 18

        elif 'sum' == de.visualization:
            try:
                visualization = result[axis[0]].sum()
            except TypeError as ex:
                visualization = 'Error: ' + str(ex)
        elif 'average' == de.visualization:
            try:
                visualization = result[axis[0]].sum() / len(result[axis[0]])
            except Exception as ex:
                log.exception(str(ex))
                visualization = 'Error: ' + str(ex)
        else:
            return redirect('/error', params={'detail': '%s not supported' % de.visualization})
        return dict(
            extraction=extraction, visualization=visualization,
            visualization_type=de.visualization, axis=axis,
            columns=result.columns, results=result.itertuples(), count=len(result)
        )
