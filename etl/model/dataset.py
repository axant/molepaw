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
from functools import partial
import logging


log = logging.getLogger(__name__)


DST_CACHE = Cache('DST')

DEFAULT_LIMIT_FOR_PERFORMANCE = 100


def convert_dtypes(dataframe):
    cols = list(dataframe)
    for col in cols:
        if dataframe[col].dtype.name == 'object':
            counter = collections.Counter(boolean=0, datetime=0, numeric=0, object=0)
            for element in dataframe[col]:
                if is_boolean(element):
                    counter['boolean'] += 1
                elif is_datetime(element):
                    counter['datetime'] += 1
                elif is_number(element):
                    counter['numeric'] += 1
                else:
                    counter['object'] += 1
            if counter.most_common(1)[0][0] == 'boolean' and counter.most_common(2)[1][1] == 0:
                dataframe[col] = dataframe[col].astype('bool', errors='ignore')
                log.debug('column: %s type: %s (%s)', col, 'bool', dataframe[col].dtype.name)
            elif counter.most_common(1)[0][0] == 'datetime':
                dataframe[col] = pd.to_datetime(dataframe[col], errors='coerce')
                log.debug('column: %s type: %s (%s)', col, 'datetime', dataframe[col].dtype.name)
            elif counter.most_common(1)[0][0] == 'numeric':
                dataframe[col] = pd.to_numeric(dataframe[col], errors='coerce')
                log.debug('column: %s type: %s (%s)', col, 'numeric', dataframe[col].dtype.name)
        elif dataframe[col].dtype.name.startswith('float'):
            if all((element % 1 == 0 for element in dataframe[col].fillna(0))):
                dataframe[col] = dataframe[col].fillna(0).astype('int64')
                log.debug('column: %s from float to int filled with 0', col)
    return dataframe


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
        # dataframe.convert_dtypes is new in pandas version 1.0.0, not available on py2.7
        # We override it anyway because pandas.array.IntegerArray and similar are still experimental
        # even if pandas uses them anyway. also we get consistence between python2 and 3
        # we could say instead of using the best dtype, this uses appropriate one
        dataframe.convert_dtypes = partial(convert_dtypes, dataframe)
        return dataframe.convert_dtypes()

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
