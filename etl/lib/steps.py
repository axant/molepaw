# -*- coding: utf-8 -*-
import pandas
import datetime
import numpy as np
from markupsafe import Markup
from tw2.core import Validator
from tw2.forms import TextField, SingleSelectField
from tg.i18n import lazy_ugettext as l_
from etl.lib.utils import force_text
from etl.lib.validators import CommaSeparatedListValidator

try:
    unicode('test Python2')
except Exception:  # pragma: no cover
    unicode = str

def slice_dataframe(df, fields):
    """Returns a subset of the columns from the DataFrame"""
    return df[list(fields)]
slice_dataframe.form_fields = [
    TextField('fields', label=l_('Fields'), validator=CommaSeparatedListValidator(required=True),
              value='{{.options.fields}}', placeholder='comma separated fields (name, surname, age)')
]


def group(df, aggregation, **kwargs):
    """Groups the data by one or more columns and applies an aggregation function"""
    g = df.groupby(as_index=bool(kwargs.pop('as_index', False)), **kwargs)
    return g.agg(aggregation)
group.form_fields = [
    TextField('by', label=l_('Group By'), validator=CommaSeparatedListValidator(required=True),
              value='{{.options.by}}', placeholder='comma separated fields (name, surname, age)'),
    SingleSelectField('aggregation', label=l_('Aggregation Function'), validator=Validator(required=True),
                      attrs=dict(value='{{.options.aggregation}}'), prompt_text=None,
                      options=[('sum', 'Sum'), ('count', 'Count'), ('avg', 'Average')])
]


def setvalue(df, field, value):
    """Set all the values in a column with the provided one.

    If the column does not exists a new one is created.
    The value can be a numerical expression that calculates the
    value from existing columns.

    Special values:

        * @utcnow -> current date and time in UTC
        * @nan -> NaN
        * @null -> None
    """

    expr = '{} = {}'.format(field, value)
    df.eval(expr, engine='python', inplace=True, local_dict={
        'null': None,
        'nan': np.nan,
        'utcnow': np.datetime64(datetime.datetime.utcnow()),
    })
    return df


setvalue.form_fields = [
    TextField('field', label=l_('Field'), validator=Validator(required=True),
              value='{{.options.field}}'),
    TextField('value', label=l_('Value or Expression'), validator=Validator(required=True),
              value='{{.options.value}}',
              placeholder='1')
]


def striptime(df, field):
    """Removes time from a date"""
    def _striptime(series):
        try:
            v = series[field]
            return v.date()
        except:
            return None
    df[field] = df.apply(_striptime, axis='columns')
    return df
striptime.form_fields = [
    TextField('field', label=l_('Field'), validator=Validator(required=True),
              value='{{.options.field}}')
]


def stripday(df, field):
    """Removes day from a date"""
    def _stripday(series):
        try:
            v = series[field]
            return datetime.date(v.year, v.month, 1)
        except Exception as e:
            return None
    df[field] = df.apply(_stripday, axis='columns')
    return df
stripday.form_fields = [
    TextField('field', label=l_('Field'), validator=Validator(required=True),
              value='{{.options.field}}')
]


def timeago(df, field):
    """Converts a date to a delta from now (UTC) to that date."""
    utcnow = pandas.Timestamp.utcnow()
    def _calc_timeago(series):
        try:
            v = series[field]
            if pandas.isnull(v):
                return None
            return (utcnow.date() - v.date()).days
        except Exception as e:
            print('exception', e)
            return None
    df[field] = df.apply(_calc_timeago, axis='columns')
    return df
timeago.form_fields = [
    TextField('field', label=l_('Field'), validator=Validator(required=True),
              value='{{.options.field}}')
]


def rename(df, source, target):
    """Renames a column"""
    df.rename(columns={source: target}, inplace=True)
    return df
rename.form_fields = [
    TextField('source', label=l_('Field Name'), validator=Validator(required=True),
              value='{{.options.source}}'),
    TextField('target', label=l_('New Name'), validator=Validator(required=True),
              value='{{.options.target}}')
]


def query(df, expression):
    """Filters the rows for those matching the given expression.

    - Use "value != value" to get only rows where value is NaN
    - Use "value == value" to get only rows where value is not NaN

    Special values:

    * @utcnow -> current date and time in UTC
    * @nan -> NaN
    * @null -> None
    """
    return df.query(expression, local_dict={
        'null': None,
        'nan': np.nan,
        'utcnow': datetime.datetime.utcnow()
    })
query.form_fields = [
    TextField('expression', label=l_('Expression'), validator=Validator(required=True),
              value='{{.options.expression}}'),
]


def setindex(df, index):
    """Marks the Given column as the index of the data"""
    def _stringyindex(series):  # pragma: no cover
        # no cover because of py2 and 3 compatibility. (we should make pragma for specific python version)
        # this code is tested in etl/tests/functional/test_steps.py
        v = series[index]
        if isinstance(v, bytes):
            return unicode(v, 'utf-8').encode('ascii', 'replace')
        elif isinstance(v, unicode):
            return v.encode('ascii', 'replace')
        else:
            return v
    df[index] = df.apply(_stringyindex, axis='columns')
    return df.set_index(index)
setindex.form_fields = [
    TextField('index', label=l_('Field'), validator=Validator(required=True),
              value='{{.options.index}}'),
]


def concatcols(df, columns):
    """Merges two or more columns in a single one"""
    def _concat(*args):
        strs = [force_text(arg) for arg in args if not pandas.isnull(arg)]
        return '_'.join(strs) if strs else np.nan
    np_concat = np.vectorize(_concat)

    cols = [df[colname] for colname in columns]
    df['_'.join(columns)] = np_concat(*cols)
    return df
concatcols.form_fields = [
    TextField('columns', label=l_('Fields'), validator=CommaSeparatedListValidator(required=True),
              value='{{.options.columns}}', placeholder='comma separated fields (name, surname, age)')
]


def sort(df, columns):
    """Sort the data by the given columns.

    Columns are comma separated and -column can be used
    to sort in reverse order.
    """
    ascending = [False if col.startswith('-') else True for col in columns]
    colnames = [col if not col.startswith('-') else col[1:] for col in columns]
    df.sort_values(colnames, ascending=ascending, inplace=True)
    return df
sort.form_fields = [
    TextField('columns', label=l_('Fields'), validator=CommaSeparatedListValidator(required=True),
              value='{{.options.columns}}', placeholder='comma separated fields (name, surname, age)')
]


def linkize(df, field, url, name=None):
    """Convert the values to links to an URL.

    URL is processed with string formatting language,
    if you want to put the value of the field inside the URL
    use the {} placeholder.

    For example http//www.google.it/{} will lead to http://www.google.it/5
    when field value is 5.

    If you want a button in place of the link value just fill the optional
    `Button text` value to obtain a button.
    """
    def _linkize(series):
        try:
            urls = url.format(series[field])
            text = name if name else urls
            cls = "btn btn-info" if name else ""
            return Markup('<a class="{}" href="{}">{}</a>'.format(cls, urls, text))
        except Exception as e:
            return None
    df[field] = df.apply(_linkize, axis='columns')
    return df
linkize.form_fields = [
    TextField('field', label=l_('Field'), validator=Validator(required=True),
              value='{{.options.field}}'),
    TextField('url', label=l_('URL'), validator=Validator(required=True),
              value='{{.options.url}}'),
    TextField('name', label=l_('Button text'), value='{{.options.name}}')
]

def cast_to_int(df, fields):
    """Cast the fields to integer, actually string formatting is used,
    so it is only for display purpose"""
    def _cast_to_int(series, field):
        return '{:.0f}'.format(series[field])
    for field in fields:
        df[field] = df.apply(_cast_to_int, axis='columns', args=(field,))
    return df
cast_to_int.form_fields = [
    TextField('fields', label=l_('Fields'), validator=CommaSeparatedListValidator(required=True),
              value='{{.options.fields}}', placeholder='comma separated fields (name, surname, age)')
]
