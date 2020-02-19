# -*- coding: iso-8859-1 -*-
import tg
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, Column, event, inspect
from sqlalchemy.types import Integer, Unicode
import pandas as pd
import collections
from beaker.cache import Cache
from etl.model import DeclarativeBase
from etl.lib.widgets import CodeTextArea, SmartWidgetTypes
from etl.lib.helpers import is_number, is_boolean, is_datetime
import logging


log = logging.getLogger(__name__)


DST_CACHE = Cache('DST')


class DataSet(DeclarativeBase):
    __tablename__ = 'datasets'

    uid = Column(Integer, primary_key=True)
    name = Column(Unicode(99), nullable=False)
    query = Column(Unicode(2048), nullable=False)

    datasource_id = Column(Integer, ForeignKey('datasources.uid'), index=True)
    datasource = relationship('Datasource', uselist=False)

    class __sprox__(object):
        omit_fields = ['datasource_id']
        field_widget_types = SmartWidgetTypes({
            'query': CodeTextArea(type='sql')
        })

    @property
    def cache_key(self):
        return '%s%s' % (self.__tablename__, str(self.uid))

    @staticmethod
    def get_column_typed(sample, data):
        for i in sample.columns:
            if collections.Counter(
                    [is_boolean(j) for j in sample[i].tolist()]
            ).most_common(1)[0][0]:
                log.info('column: %s type: %s' % (i, 'bool'))
                data[i] = data[i].astype('bool', errors='ignore')
            elif collections.Counter(
                    [is_datetime(j) for j in sample[i].tolist()]
            ).most_common(1)[0][0]:
                log.info('column: %s type: %s' % (i, 'datetime'))
                data[i] = pd.to_datetime(data[i], errors='coerce')
            elif collections.Counter(
                    [is_number(j) for j in sample[i].tolist()]
            ).most_common(1)[0][0]:
                log.info('column: %s type: %s' % (i, 'numeric'))
                data[i] = pd.to_numeric(data[i], errors='coerce')
            return data

    @property
    def sample(self):
        try:
            return DST_CACHE.get_value(self.cache_key)
        except KeyError:
            df = self.datasource.dbsession.execute(self.query)
            df = df.sample(100) if len(df.index) >= 100 else df
            cache = self.get_column_typed(df, df)
            DST_CACHE.set_value(
                self.cache_key,
                cache
            )
            return cache

    def fetch(self):
        if not self.datasource:
            raise ValueError('DataSet is not bound to any Datasource')

        def get_data():
            try:
                df = self.datasource.dbsession.execute(self.query)
                sample_df = df.sample(100) if len(df.index) >= 100 else df
                return self.get_column_typed(sample_df, df)
            except:
                self.datasource.dbsession.rollback()
                raise

        cache = tg.cache.get_cache('datasets_cache', expire=1800)

        cached_value = cache.get_value(
            key=self.cache_key,
            createfunc=get_data,
            expiretime=1800
        )
        return cached_value


@event.listens_for(DataSet, 'before_update')
def receive_before_update(mapper, connection, target):
    fields = ['query', 'datasource_id']
    state = inspect(target)
    for field in fields:
        _attr = state.attrs.get(field)
        history = _attr.load_history()
        if history.has_changes():
            DST_CACHE.remove_value(target.cache_key)
            try:
                cache = tg.cache.get_cache('datasets_cache', expire=1800)
                cache.remove_value(target.cache_key)
            except:
                pass


@event.listens_for(DataSet, 'before_delete')
def receive_before_update(mapper, connection, target):
    DST_CACHE.remove_value(target.cache_key)
    try:
        cache = tg.cache.get_cache('datasets_cache', expire=1800)
        cache.remove_value(target.cache_key)
    except:
        pass
