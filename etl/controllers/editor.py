# -*- coding: utf-8 -*-
"""Extractions Editor controller module"""
import itertools
import json
import logging
import tg
from markupsafe import Markup
from formencode import validators
from tg import expose, redirect, validate, flash, abort, RestController, tmpl_context, decode_params, \
    response, validation_errors_response
from tg import predicates
from tg.validation import Convert
from webhelpers2.text import truncate
from tg.i18n import ugettext as _
from etl.lib.utils import stringfy_exc, force_text
from etl.lib.validators import VisualizationTypeValidator, MergeValidatorSchema,\
    validate_axis_against_extraction_visualization
from etl.model import DBSession, Extraction, ExtractionStep, DataSet, ExtractionDataSet
from etl.model.extraction import VISUALIZATION_TYPES
from etl.model.extractionstep import FUNCTIONS
from etl.lib.helpers import escape_string_to_js
import sys
py_version = sys.version_info[:2][0]
log = logging.getLogger('molepaw')


class DatasetsEditorController(RestController):
    @expose('json')
    def get_all(self):
        try:
            data = tmpl_context.extraction.fetch()
            sampledata = dict(
                errors=None,
                columns=(col.decode('utf-8', "replace") if (isinstance(col, str) and py_version < 3) else col for col in data.columns),
                data=list(
                    itertools.islice(([force_text(tv) for tv in t] for t in data.itertuples()), 1)
                ))
        except Exception as e:
            log.exception('Unable to retrieve sample dataset data')
            sampledata = dict(errors=str(e),
                              columns=[],
                              data=[])
        return dict(datasets=tmpl_context.extraction.datasets,
                    sampledata=sampledata)

    @expose('json')
    @decode_params('json')
    @validate(validators=MergeValidatorSchema(), error_handler=validation_errors_response)
    def post(self, datasetid=None, join_type=None, join_self_col=None, join_other_col=None, **kwargs):
        try:
            priority = tmpl_context.extraction.datasets[-1].priority + 1
        except:
            priority = 0

        DBSession.add(ExtractionDataSet(extraction=tmpl_context.extraction,
                                        dataset_id=datasetid,
                                        priority=priority,
                                        join_type=join_type,
                                        join_self_col=join_self_col,
                                        join_other_col=join_other_col))
        return dict()

    @expose('json')
    @decode_params('json')
    @validate({
        'uid': validators.Int(not_empty=True),
        'datasetid': validators.Int(not_empty=True),
    }, error_handler=validation_errors_response)
    def put(self, uid=None, datasetid=None, join_type=None, join_self_col=None, join_other_col=None):
        DBSession.query(ExtractionDataSet).filter_by(uid=uid).update({
            'dataset_id': datasetid,
            'join_type': join_type,
            'join_self_col': join_self_col,
            'join_other_col': join_other_col,
        })
        return dict(
            join_type=join_type,
            join_self_col=join_self_col,
            join_other_col=join_other_col,
        )

    @expose('json')
    @validate({'uid': validators.Int(not_empty=True)}, error_handler=validation_errors_response)
    def delete(self, uid, **kwargs):
        dataset = DBSession.query(ExtractionDataSet).filter_by(uid=uid).first()
        if dataset:
            DBSession.delete(dataset)
        return dict()


class StepsEditorController(RestController):
    @expose('json')
    def get_all(self):
        return dict(steps=tmpl_context.extraction.steps)

    @expose('json')
    @decode_params('json')
    def put(self, uid=None, function=None, priority=None, options=None, **kwargs):
        step = DBSession.query(ExtractionStep).get(uid) or abort(404)
        if function is not None:
            step.function = function

        if priority is not None:
            step.priority = priority

        if options is not None:
            try:
                step.options = json.dumps(ExtractionStep.formfor(function or step.function).validate(options))
            except Exception as e:
                response.status = 412
                return dict(errors=str(e))

        return dict(step=step)

    @expose('json')
    @decode_params('json')
    def post(self, function=None, priority=None, options=None, **kwargs):
        try:
            options = ExtractionStep.formfor(function).validate(options)
        except Exception as e:
            response.status = 412
            return dict(errors=str(e))

        DBSession.add(ExtractionStep(
            extraction_id=tmpl_context.extraction.uid,
            function=function,
            priority=priority,
            options=json.dumps(options)
        ))
        return dict()

    @expose('json')
    @decode_params('json')
    def delete(self, uid=None, **kwargs):
        step = DBSession.query(ExtractionStep).get(uid) or abort(404, passthrough='json')
        DBSession.delete(step)
        return dict()

    @expose('json')
    @decode_params('json')
    @validate({
        'enabled': Convert(int, default=0)
    }, error_handler=validation_errors_response)
    def toggle(self, uid=None, enabled=False, **kwargs):
        step = DBSession.query(ExtractionStep).get(uid) or abort(404)
        step.enabled = enabled
        return dict()


class StepFunctionController(RestController):
    @expose('json')
    def get_one(self, func):
        try:
            step = FUNCTIONS[func]
        except:
            abort(404)

        return dict(name=func, doc=step.__doc__)


class EditorController(RestController):
    allow_only = predicates.not_anonymous()

    function = StepFunctionController()
    datasets = DatasetsEditorController()
    steps = StepsEditorController()

    def _visit(self, extraction=None, *args, **kwargs):
        try:
            tmpl_context.extraction = DBSession.query(Extraction).filter_by(uid=extraction).one()
        except:
            abort(404)

    @expose('genshi:etl.templates.editor.index')
    @validate({'extraction': Convert(lambda v: DBSession.query(Extraction).filter_by(uid=v).one())},
              error_handler=abort(404, error_handler=True))
    def get_one(self, extraction=None, *args, **kw):
        available_datasets = []
        datasets_columns = {}

        for d in DBSession.query(DataSet):
            try:
                cols = [str(c) for c in d.fetch().columns]
            except:
                cols = []
            available_datasets.append((d.uid, d.name))
            datasets_columns[d.uid] = cols

        # Documentation of all the functions available to build extractions
        docstring = {key: value.__doc__ for (key, value) in list(FUNCTIONS.items())}
        docstring = escape_string_to_js(docstring)

        from tgext.pluggable import app_model
        categories = DBSession.query(app_model.Category)

        return dict(extraction=extraction,
                    stepsformfields=dict((fname, f.form_fields) for fname,f in list(FUNCTIONS.items())),
                    available_datasets=available_datasets, datasets_columns=datasets_columns,
                    visualization_types=VISUALIZATION_TYPES, docstring=json.dumps(docstring),
                    category_list=categories)

    @expose('json')
    @decode_params('json')
    @validate({'extraction': Convert(lambda v: DBSession.query(Extraction).filter_by(uid=v).one()),
               'visualization': VisualizationTypeValidator()},
              error_handler=abort(404, error_handler=True))
    def post(self, extraction=None, visualization=None, *args, **kw):
        
        if visualization['axis']:
            validate_axis_against_extraction_visualization(
                visualization['type'],
                visualization['axis'],
                extraction
            )

        extraction.visualization = visualization['type']
        extraction.graph_axis = visualization['axis']
        return dict(extraction=extraction)

    @expose('json')
    @validate({'extraction': Convert(lambda v: DBSession.query(Extraction).filter_by(uid=v).one())},
              error_handler=abort(404, error_handler=True))
    def test_pipeline(self, extraction=None):
        try:
            data = extraction.fetch()
        except Exception as e:
            return dict(result=[dict(errors=stringfy_exc(e)[0], columns=[], data=[])])

        result = []
        for step in extraction.steps:
            try:
                data = step.apply(data)
                result.append(dict(errors=None,
                                   columns=(str(col) for col in data.columns),
                                   data=list(((truncate(force_text(d), 50) for d in r) for r in itertools.islice(
                                       data.itertuples(), 3
                                   )))))
            except Exception as e:
                log.exception(e)
                result.append(dict(errors=stringfy_exc(e)[0], columns=[], data=[]))

        return dict(results=result)

    @expose('json')
    def save_category(self, extraction, category):
        tmpl_context.extraction.category_id = category if category != "-1" else None
        flash(_('Category correctly updated'))

        return redirect(tg.url(['/editor', str(tmpl_context.extraction.uid)]))
