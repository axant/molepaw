# -*- coding: utf-8 -*-
"""Extractions controller module"""
import json
import logging
import pandas.tseries
import sys
import tg
from tg import expose, redirect, validate, flash, url, abort, request, require, RestController, decode_params
from tg import predicates, lurl, config
from tg.util import Bunch
from tg.validation import Convert
import tw2.forms as twf
import tw2.core as twc
import axf.bootstrap

from etl.lib.utils import dateframe_to_csv, is_api_authenticated, dateframe_to_json
from etl.lib.base import BaseController
from etl.model import DBSession, Extraction, ExtractionFilter
from etl.lib.helpers import get_graph
from etl.model.extractionstep import ExtractionStep

from pandas import DataFrame
from tgext.pluggable import app_model

try:
    unicode('test Python2')
except Exception:               # PRAGMA NO COVER
    unicode = str  # this is bad
py_version = sys.version_info[:2][0]
log = logging.getLogger('molepaw')


LINECHART_SUPPORTED_INDEXES = [
    pandas.Index,
    pandas.DatetimeIndex,
    pandas.Int64Index,
    pandas.Float64Index,
]


class CreateExtractionForm(twf.Form):
    class child(axf.bootstrap.BootstrapFormLayout):
        name = twf.TextField(label='Extraction Name',
                             validator=twc.Validator(required=True),
                             css_class="new_extraction_input")

    action = lurl('/extractions/create')
    submit = twf.SubmitButton(value='Create', css_class='btn btn-default')


class ExtractionFilterController(RestController):

    @expose('json')
    @decode_params('json')
    @validate({'extraction': Convert(lambda v: DBSession.query(Extraction).filter_by(uid=v).one())},
              error_handler=abort(404, error_handler=True))
    def post(self, filter=None, extraction=None, **kwargs):
        e_filter = ExtractionFilter(extraction=extraction, name=filter.get('name'))

        if filter.get('default'):
            ExtractionFilter.set_default(e_filter)

        DBSession.add(ExtractionStep(
            extraction_filter=e_filter,
            function='query',
            priority=0,
            options=json.dumps({'expression': filter.get('query')})
        ))

        DBSession.flush()
        return dict(filter=e_filter)

    @expose()
    def delete(self, uid=None):
        e_filter = DBSession.query(ExtractionFilter).get(uid)
        if not e_filter:
            abort(404)
        extraction_id = e_filter.extraction_id
        DBSession.delete(e_filter)
        return redirect('/extractions/view/%s' % extraction_id)

    @expose('json')
    @decode_params('json')
    @validate({'extraction': Convert(lambda v: DBSession.query(Extraction).filter_by(uid=v).one())},
              error_handler=abort(404, error_handler=True))
    def put(self, filter=None, extraction=None, **kwargs):
        e_filter = DBSession.query(ExtractionFilter).get(filter.get('uid'))
        if not e_filter:
            return abort(404)
        step = DBSession.query(ExtractionStep).get(filter.get('steps')[0]['uid'])
        if not step:
            return abort(404)
        e_filter.extraction = extraction
        e_filter.name = filter.get('name')
        if filter.get('default'):
            ExtractionFilter.set_default(e_filter)
        else:
            e_filter.default = False
        exp = {'expression': filter.get('query')}
        step.options = json.dumps(exp)
        return dict(filter=e_filter)


class ExtractionsController(BaseController):

    filter = ExtractionFilterController()

    @expose('etl.templates.extractions.index')
    @require(predicates.not_anonymous())
    def index(self, **kw):
        categories = DBSession.query(app_model.Category).all()
        uncategorised = DBSession.query(Extraction).filter_by(category_id=None).all()
        categories += [Bunch(extractions=uncategorised, name="No Category")]
        return dict(categories=categories,
                    has_validation_errors=request.validation.errors,
                    new_form=CreateExtractionForm)

    @expose()
    @require(predicates.in_group('managers'))
    @validate(CreateExtractionForm, error_handler=index)
    def create(self, name, **kw):
        DBSession.add(Extraction(name=name))
        flash('New Extraction successfully created', 'ok')
        return redirect('./index')

    @expose()
    @require(predicates.in_any_group('manager', 'admin'))
    def delete(self, uid):
        extraction = DBSession.query(Extraction).get(uid) or abort(404)
        DBSession.delete(extraction)
        flash('Extraction correctly deleted')
        return redirect(tg.url('/extractions'))

    @expose('etl.templates.extractions.view')
    @expose(content_type="text/csv")
    @expose(content_type='application/json')
    @require(predicates.Any(predicates.not_anonymous(), is_api_authenticated()))
    @validate({'extraction': Convert(lambda v: DBSession.query(Extraction).filter_by(uid=v).one())},
              error_handler=abort(404, error_handler=True))
    def view(self, extraction, extraction_filter=None, **kw):
        try:
            result = extraction.perform()
        except Exception as e:
            log.exception('Failed to Retrieve Data')
            flash('ERROR RETRIEVING DATA: %s' % e, 'error')
            return redirect('/error')
        e_filter = None

        try:
            if extraction_filter:
                if int(extraction_filter) != -1:  # -1 = original extraction requested by user
                    e_filter = DBSession.query(ExtractionFilter).get(extraction_filter)
                    if not e_filter:
                        return abort(404)
                    result = e_filter.perform(result)
            else:
                default = DBSession.query(ExtractionFilter).filter(
                    ExtractionFilter.default == True,
                    ExtractionFilter.extraction_id == extraction.uid
                ).first()
                if default:
                    e_filter = default
                    result = default.perform(result)
        except Exception as e:
            log.exception('Failed to Retrieve Data')
            flash('ERROR RETRIEVING DATA: %s' % e, 'error')
            result = DataFrame()

        if request.response_type == 'text/csv':
            return dateframe_to_csv(result)
        elif request.response_type == 'application/json':
            return dateframe_to_json(result)

        visualizations = dict((name, None) for name in extraction.visualization.split('+'))
        axis = []
        if extraction.graph_axis:
            axis = [x.strip() for x in extraction.graph_axis.split(',')]

        visualizations = get_graph(result, axis, visualizations)

        if config.get("extraction.max_elements") is None:
            log.warn("Cannot find max elements to render in config file. Using default 10000")
        if len(result) * len(result.columns) > int(config.get("extraction.max_elements", 10000)):
            flash("There are too many data to extract, please add some filters", "error")
        filters = DBSession.query(ExtractionFilter).filter_by(extraction_id=extraction.uid).all()
        return dict(
            extraction=extraction,
            visualizations=visualizations,
            columns=result.columns,
            results=result.itertuples(),
            count=len(result),
            filters=filters,
            extraction_filter=e_filter,
            py2=py_version < 3
        )
