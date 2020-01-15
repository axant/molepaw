# -*- coding: utf-8 -*-
"""Extraction model module."""
import pandas
from pandas import DataFrame
from sqlalchemy import *
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.ext.declarative import synonym_for
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.types import Integer, Unicode, DateTime, LargeBinary, Enum
from sqlalchemy.orm import relationship, backref, class_mapper
from tgext.pluggable import LazyForeignKey, app_model
from tw2.core import Deferred
from tw2.forms import SingleSelectField

from etl.lib.widgets import SmartWidgetTypes
from etl.model import DeclarativeBase, metadata, DBSession

VISUALIZATION_TYPES = [('table', 'Table'),
                       ('histogram', 'Histogram'),
                       ('table+histogram', 'Histogram & Table'),
                       ('linechart', 'Line Chart'),
                       ('table+linechart', 'Line Chart & Table'),
                       ('pie', 'Pie'),
                       ('table+pie', 'Pie & Table')]

class Extraction(DeclarativeBase):
    __tablename__ = 'extractions'


    class __sprox__(object):
        possible_field_names = {
            'datasets': ['descr'],
            'steps': ['desc']
        }
        field_widget_types = SmartWidgetTypes({
            'visualization': SingleSelectField
        })
        field_widget_args = {
            'visualization': {'prompt_text': None,
                              'options': VISUALIZATION_TYPES
                              }
        }

    uid = Column(Integer, primary_key=True)
    name = Column(Unicode(99), nullable=False)
    visualization = Column(Unicode(64), default='table', nullable=False)
    category_id = Column(Integer, LazyForeignKey(lambda: app_model.Category._id), nullable=True)
    category = relationship(lambda: app_model.Category, backref=backref("extractions"))
    graph_axis = Column(Unicode(64), nullable=True)
    datasets = relationship('ExtractionDataSet', cascade='all, delete-orphan', order_by="ExtractionDataSet.priority")
    steps = relationship('ExtractionStep', cascade='all, delete-orphan', order_by="ExtractionStep.priority")

    def fetch(self):
        if not self.datasets:
            return DataFrame()

        extdatasets = iter(self.datasets)
        df = next(extdatasets).dataset.fetch()

        for extdataset in extdatasets:
            df = pandas.merge(df, extdataset.dataset.fetch(),
                              how=extdataset.join_type,
                              left_on=extdataset.join_other_col,
                              right_on=extdataset.join_self_col,
                              suffixes=('', '_j_'+extdataset.dataset.name.lower()))

        return df

    def perform(self):
        print(self)
        df = self.fetch()
        print(df)

        for step in self.steps:
            df = step.apply(df)

        return df


class ExtractionDataSet(DeclarativeBase):
    __tablename__ = 'extraction_datasets'

    uid = Column(Integer, primary_key=True)
    priority = Column(Integer, default=0, nullable=False)
    dataset_id = Column(Integer, ForeignKey('datasets.uid'), index=True)
    dataset = relationship('DataSet', uselist=False)
    extraction_id = Column(Integer, ForeignKey('extractions.uid'), index=True)
    extraction = relationship('Extraction', uselist=False)

    join_type = Column(Unicode(64), default='left')
    join_self_col = Column(Unicode(64), default=None)
    join_other_col = Column(Unicode(64), default=None)

    class __sprox__(object):
        hide_fields = ['uid']
        field_order = ['extraction', 'dataset', 'priority', 'join_type']
        omit_fields = ['dataset_id', 'extraction_id', 'descr']
        field_widget_types = SmartWidgetTypes({
            'join_type': SingleSelectField
        })
        field_widget_args = {
            'join_type': {'prompt_text': None,
                          'options': ['inner', 'left', 'right', 'outer']},
        }

    def __json__(self):
        return dict(
            uid=self.uid,
            priority=self.priority,
            dataset_id=self.dataset_id,
            extraction_id=self.extraction_id,
            join_type=self.join_type,
            join_self_col=self.join_self_col,
            join_other_col=self.join_other_col,
            name=self.dataset.name,
            datasource=self.dataset.datasource.name,
        )

    @synonym_for('dataset_id')
    @property
    def descr(self):
        s = '{} {} join'.format(self.dataset.name, self.join_type)
        if self.join_self_col and self.join_other_col:
            s += ' on {} = {}'.format(self.join_self_col, self.join_other_col)
        return s

__all__ = ['Extraction']
