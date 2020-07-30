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

DEFAULT_LIMIT_FOR_PERFORMANCE = 100


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

    def cache_key(self, limit=None):
        return '%s%s-%s' % (self.__tablename__, self.uid, limit)

    @property
    def sample(self):
        try:
            return DST_CACHE.get_value(self.cache_key(DEFAULT_LIMIT_FOR_PERFORMANCE))
        except KeyError:
            df = self.datasource.dbsession.execute(self.query, limit=DEFAULT_LIMIT_FOR_PERFORMANCE)
            cache = self.get_column_typed(df)
            DST_CACHE.set_value(
                self.cache_key(DEFAULT_LIMIT_FOR_PERFORMANCE),
                cache
            )
            return cache

    @staticmethod
    def get_column_typed(dataframe):
        cols = list(dataframe)
        for i in cols:
            # if it's not an object it means we should already have the right type
            if dataframe[i].dtype.name == 'object':
                if all([is_boolean(j) for j in dataframe[i]]):
                    log.debug('column: %s type: %s', i, 'bool')
                    dataframe[i] = dataframe[i].astype('bool', errors='ignore')
                elif collections.Counter(
                        [is_datetime(j) for j in dataframe[i]]
                ).most_common(1)[0][0]:
                    log.debug('column: %s type: %s', i, 'datetime')
                    dataframe[i] = pd.to_datetime(dataframe[i], errors='coerce')
                elif collections.Counter(
                        [is_number(j) for j in dataframe[i]]
                ).most_common(1)[0][0]:
                    log.debug('column: %s type: %s', i, 'numeric')
                    dataframe[i] = pd.to_numeric(dataframe[i], errors='coerce')
        return dataframe

    def fetch(self, limit=None):
        if not self.datasource:
            raise ValueError('DataSet is not bound to any Datasource')

        def get_data():
            try:
                df = self.datasource.dbsession.execute(self.query, limit=limit)
                return self.get_column_typed(df)
            except:
                self.datasource.dbsession.rollback()
                raise

        cache = tg.cache.get_cache('datasets_cache', expire=1800)

        return cache.get_value(
            key=self.cache_key(limit),
            createfunc=get_data,
            expiretime=1800
        )


def empty_cache(cache_key):
    DST_CACHE.remove_value(cache_key)
    try:
        cache = tg.cache.get_cache('datasets_cache', expire=1800)
        cache.remove_value(cache_key)
    except:  # PRAGMA NO COVER
        pass

# well, the cache should be invalidated even for limit specified datasets
# even for values different from default
@event.listens_for(DataSet, 'before_update')
def receive_before_update(mapper, connection, target):
    fields = ['query', 'datasource_id']
    state = inspect(target)
    for field in fields:
        _attr = state.attrs.get(field)
        history = _attr.load_history()
        if history.has_changes():
            empty_cache(target.cache_key())
            empty_cache(target.cache_key(DEFAULT_LIMIT_FOR_PERFORMANCE))


@event.listens_for(DataSet, 'before_delete')
def receive_before_delete(mapper, connection, target):
    empty_cache(target.cache_key())
    empty_cache(target.cache_key(DEFAULT_LIMIT_FOR_PERFORMANCE))
