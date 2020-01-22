# -*- coding: utf-8 -*-
import json
from markupsafe import Markup
from tw2.core import Validator, ValidationError
from tg import tmpl_context, abort
from etl.model.extraction import VISUALIZATION_TYPES
from etl.model.dataset import DataSet
from etl.model import DBSession
from formencode.schema import Schema
from formencode.api import Invalid
from formencode import validators
import pandas as pd
from datetime import datetime


class MergeValidator(validators.FieldsMatch):
    validate_partial_form = True

    def _validate_python(self, value_dict, state=None):
        if 'join_type' not in value_dict.keys() and 'join_other_col' not in value_dict.keys()\
                and 'join_self_col' not in value_dict.keys():
            return None
        else:
            extraction = tmpl_context.extraction
            df = extraction.fetch()
            try:
                dataset = DBSession.query(DataSet).get(int(value_dict['datasetid']))
                pd.merge(
                    df,
                    dataset.fetch(),
                    how=value_dict['join_type'],
                    left_on=value_dict['join_other_col'],
                    right_on=value_dict['join_self_col'],
                    suffixes=('', '_j_' + dataset.name.lower())
                )
                return None
            except ValueError as ex:
                raise Invalid(
                    ex.__repr__(),
                    value_dict,
                    state,
                    error_dict={}
                )


class MergeValidatorSchema(Schema):
    allow_extra_fields = True
    datasetid = validators.NotEmpty()
    chained_validators = [MergeValidator('datasetid', 'join_type', 'join_self_col', 'join_other_col'), ]


class JSONValidator(Validator):
    def _validate_python(self, value, state=None):
        try:
            json.loads(value)
        except:
            raise ValidationError('Invalid JSON', self)


class CommaSeparatedListValidator(Validator):
    def _convert_to_python(self, value, state=None):
        return [x.strip() for x in value.split(',')]

    def _convert_from_python(self, value, state=None):
        if isinstance(value, list):
            return ','.join(value)
        return value


class VisualizationTypeValidator(Validator):
    def _validate_python(self, value, state=None):
        if value['type'] not in [v_type[0] for v_type in VISUALIZATION_TYPES]:
            raise ValidationError('Not a valid Visualization Type', self)


def validate_axis_against_extraction_visualization(
        visualization_type,
        user_axis,
        extraction
):
    axis = [x.strip() for x in user_axis.split(',')]
    try:
        extraction.perform()[axis]  # => ['users', 'month']
    except Exception as e:
        abort(412, detail=Markup("<strong>{}</strong>".format(str(e))))

    if visualization_type in ('histogram', 'table+histogram'):
        if not (extraction.perform()[axis[0]].values.dtype == object):
            abort(412, detail=Markup("<strong>x must be a string</strong>"))

        if len(extraction.perform()[axis[0]].values.tolist()) != len(
                set(extraction.perform()[axis[0]].values.tolist())):
            abort(412, detail=Markup("<strong>histogram doens't allow multiplied</strong>"))

    if visualization_type in ('linechart', 'table+linechart'):
        if not (
                extraction.perform()[axis[0]].values.dtype and
                extraction.perform()[axis[0]].values.dtype == int
        ):
            try:
                x = [
                    datetime(year=date.year, month=date.month, day=date.day)
                    for date in pd.to_datetime(extraction.perform()[axis[0]].values)
                ]
            except Exception as e:
                abort(412, detail=Markup(
                    "<strong>Only digits and datetimes are allowed. found: %s, exception: %s</strong>" % (
                    extraction.perform()[axis[0]].values.dtype, str(e))
                ))

        if (
                len(extraction.perform()[axis[0]].values.tolist()) !=
                len(set(extraction.perform()[axis[0]].values.tolist()))  # che senso ha?
        ):
            abort(412, detail=Markup("<strong>Line chart doens't allow multiplied data</strong>"))
