# -*- coding: utf-8 -*-
import json

import pandas
from pandas import DataFrame
from sqlalchemy import *
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.ext.declarative import synonym_for
from sqlalchemy.types import Integer, Unicode, DateTime, LargeBinary, Enum
from sqlalchemy.orm import relationship, backref
from tw2.forms import SingleSelectField
from tw2.forms.widgets import BaseLayout

from etl.lib.validators import JSONValidator
from etl.lib.widgets import SmartWidgetTypes, CodeTextArea
from etl.model import DeclarativeBase, metadata, DBSession
from etl.lib import steps

FUNCTIONS = {
    'slice': steps.slice_dataframe,
    'group': steps.group,
    'striptime': steps.striptime,
    'rename': steps.rename,
    'stripday': steps.stripday,
    'concatcols': steps.concatcols,
    'setindex': steps.setindex,
    'setvalue': steps.setvalue,
    'query': steps.query,
    'sort': steps.sort,
    'timeago': steps.timeago,
    'linkize': steps.linkize,
    'cast_to_int': steps.cast_to_int,
}


class ExtractionStep(DeclarativeBase):
    __tablename__ = 'extraction_steps'

    uid = Column(Integer, primary_key=True)

    extraction_id = Column(Integer, ForeignKey('extractions.uid'), index=True)
    extraction = relationship('Extraction', uselist=False)

    extraction_filter_id = Column(Integer, ForeignKey('extraction_filters.uid'), index=True)
    extraction_filter = relationship('ExtractionFilter', uselist=False)
    priority = Column(Integer, default=0, nullable=False)
    function = Column(Unicode(99), nullable=False)
    options = Column(Unicode(2048), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)

    class __sprox__(object):
        hide_fields = ['uid']
        field_order = ['extraction', 'priority', 'function', 'options']
        omit_fields = ['extraction_id', 'descr']
        field_widget_types = SmartWidgetTypes({
            'function': SingleSelectField,
            'priority': SingleSelectField,
            'options': CodeTextArea(type='js')
        })
        field_widget_args = {
            'function': {'options': list(FUNCTIONS.keys())},
            'priority': {'options': list(range(10)),
                         'prompt_text': None}
        }
        field_validator_types = {
            'options': JSONValidator
        }

    def __json__(self):
        return dict(
            uid=self.uid,
            extraction_id=self.extraction_id,
            priority=self.priority,
            function=self.function,
            function_doc=FUNCTIONS[self.function].__doc__,
            options=json.loads(self.options),
            enabled=self.enabled,
        )

    @classmethod
    def formfor(cls, func):
        print('func', func)
        return BaseLayout(children=FUNCTIONS[func].form_fields)

    @property
    def form(self):
        return self.formfor(self.function)

    @synonym_for('function')
    @property
    def descr(self):
        return '{} : {}'.format(self.function, self.options)

    def apply(self, df):
        if not self.enabled:
            return df

        func = FUNCTIONS[self.function]
        options = json.loads(self.options)
        if isinstance(options, dict):
            return func(df, **options)
        elif isinstance(options, list):
            return func(df, *options)
        else:
            raise ValueError('Options must be either a list of values or a dictionary of options')
