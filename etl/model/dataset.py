# -*- coding: iso-8859-1 -*-
import tg
from sqlalchemy.orm import mapper, relation, relationship
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, Unicode, Boolean
import pandas as pd
import collections

from etl.model import DeclarativeBase
from etl.lib.widgets import CodeTextArea, SmartWidgetTypes
from etl.lib.helpers import is_number, is_boolean, is_datetime
import logging


log = logging.getLogger(__name__)


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

    def fetch(self):
        if not self.datasource:
            raise ValueError('DataSet is not bound to any Datasource')

        cache = tg.cache.get_cache('datasets_cache', expire=1800)
        try:
            return cache.get(str(self.uid))
        except KeyError:
            try:
                ##################### START CHECKING DATA-TYPE #####################
                df = self.datasource.dbsession.execute(self.query)
                for i in df.columns:
                    if collections.Counter(
                        [is_boolean(j) for j in df[i].head(100).tolist()]
                    ).most_common(1)[0][0]:
                        log.info('column: %s type: %s' % (i, 'bool'))
                        df[i] = df[i].astype('bool', errors='ignore')
                    elif collections.Counter(
                        [is_datetime(j) for j in df[i].head(100).tolist()]
                    ).most_common(1)[0][0]:
                        log.info('column: %s type: %s' % (i, 'datetime'))
                        df[i] = pd.to_datetime(df[i], errors='coerce')
                    elif collections.Counter(
                        [is_number(j) for j in df[i].head(100).tolist()]
                    ).most_common(1)[0][0]:
                        log.info('column: %s type: %s' % (i, 'numeric'))
                        df[i] = pd.to_numeric(df[i], errors='coerce')
                return df
                        ##################### END CHECKING DATA-TYPE ########################
            except:
                self.datasource.dbsession.rollback()
                raise
