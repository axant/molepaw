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
from etl.lib.helpers import show_graph, get_graph


class MergeValidator(validators.FieldsMatch):
    validate_partial_form = True

    def _validate_python(self, value_dict, state=None):
        if 'join_type' not in value_dict.keys() and 'join_other_col' not in value_dict.keys() \
                and 'join_self_col' not in value_dict.keys():
            return None
        else:
            extraction = tmpl_context.extraction
            df = extraction.sample
            try:
                dataset = DBSession.query(DataSet).get(int(value_dict['datasetid']))
                pd.merge(
                    df,
                    dataset.sample,
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
    data = extraction.perform(sample=True)
    visualizations = dict((name, None) for name in visualization_type.split('+'))

    try:
        data = extraction.perform(sample=True)
        data[axis]  # => ['users', 'month']
    except Exception as e:
        abort(412, detail=Markup("<strong>{}</strong>".format(str(e))))

    x_values = data[axis[0]].values
    if visualization_type in ('histogram', 'table+histogram'):
        if not (x_values.dtype == object):
            abort(412, detail=Markup("<strong>x must be a string</strong>"))

        entries = x_values.tolist()
        if len(entries) != len(set(entries)):
            abort(412, detail=Markup("<strong>histogram doens't allow duplicated values on X axis</strong>"))

    if visualization_type in ('linechart', 'table+linechart'):
        if not (x_values.dtype and x_values.dtype == int):
            try:
                x = [
                    datetime(year=date.year, month=date.month, day=date.day)
                    for date in pd.to_datetime(x_values)
                ]
            except Exception as e:
                abort(412, detail=Markup(
                    "<strong>Only digits and datetimes are allowed. found: %s, exception: %s</strong>" % (
                    x_values.dtype, str(e))
                ))

        entries = x_values.tolist()
        if len(entries) != len(set(entries)):
            abort(412, detail=Markup("<strong>Line chart doens't allow duplicated values on X axis</strong>"))

    check = len(visualizations.keys())
    if any(x in visualizations.keys() for x in ['histogram', 'pie', 'linechart']):
        try:
            visualizations = get_graph(data, axis, visualizations)
            if len(visualizations.keys()) < check:
                raise Exception('Your axis are not valid')
            for key in visualizations.keys():
                if key != 'table':
                    show_graph(visualizations[key])
        except Exception as e:
            abort(412, detail=Markup("<strong>{}</strong>".format(str(e))))
