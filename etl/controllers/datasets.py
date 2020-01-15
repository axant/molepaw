# -*- coding: iso-8859-1 -*-
"""Main Controller"""
import logging

from tg import predicates, require
from tg import expose, request, abort, validate, flash
from tg.validation import Convert
import sys
from etl.lib.base import BaseController
from etl.lib.utils import dateframe_to_csv, dateframe_to_json, is_api_authenticated
from etl.model import DBSession
from etl.model import *
py_version = sys.version_info[:2][0]
log = logging.getLogger('molepaw')


class DataSetController(BaseController):
    @expose('etl.templates.datasets.index')
    @require(predicates.not_anonymous())
    def index(self):
        datasets = DBSession.query(DataSet).all()
        return dict(datasets=datasets)

    @expose('etl.templates.datasets.view')
    @expose(content_type="text/csv")
    @expose(content_type='application/json')
    @require(predicates.Any(predicates.not_anonymous(), is_api_authenticated()))
    @validate({'dataset': Convert(lambda v: DBSession.query(DataSet).filter_by(uid=v).one())},
              error_handler=abort(404, error_handler=True))
    def view(self, dataset, **kw):
        try:
            result = dataset.fetch()
        except Exception as e:
            log.exception('Failed to Retrieve Data')
            flash('ERROR: %s' % e, 'error')
            return dict(dataset=dataset, columns=[], results=[], count=0)
        if request.response_type == 'text/csv':
            return dateframe_to_csv(result)
        elif request.response_type == 'application/json':
            return dateframe_to_json(result)

        return dict(
            dataset=dataset,
            columns=list(result.columns),
            results=list(result.itertuples()),
            count=len(result),
            py2=py_version < 3
        )
