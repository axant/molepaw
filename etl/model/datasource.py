# -*- coding: utf-8 -*-
"""Datasource model module."""
from sqlalchemy import Column, event, inspect
from sqlalchemy.types import Integer, Unicode
from tw2.forms import TextField
from beaker.cache import Cache
from etl.lib.widgets import SmartWidgetTypes
from etl.model import DeclarativeBase
from etl.lib.dbsessions import session_factory


DS_CACHE = Cache('DS')


def reset_cache():
    DS_CACHE.clear()


class Datasource(DeclarativeBase):
    __tablename__ = 'datasources'

    uid = Column(Integer, primary_key=True)
    name = Column(Unicode(99), nullable=False)
    url = Column(Unicode(255), nullable=False)

    class __sprox__(object):
        field_widget_types = SmartWidgetTypes({
            'url': TextField
        })
        field_widget_args = {
            'url': {'placeholder': 'mysql://user:password@host:port/dbname'}
        }

    @property
    def cache_key(self):
        return '%s%s' % (self.__tablename__, str(self.uid))

    @property
    def dbsession(self):
        try:
            return DS_CACHE.get_value(self.cache_key)
        except KeyError as ex:
            dbsession = session_factory(self.url)
            DS_CACHE.set_value(self.cache_key, dbsession)
            return dbsession


@event.listens_for(Datasource, 'before_update')
def receive_before_update_url(mapper, connection, target):
    state = inspect(target)
    url_attr = state.attrs.get('url')
    history = url_attr.load_history()
    if history.has_changes():
        DS_CACHE.remove_value(target.cache_key)


@event.listens_for(Datasource, 'before_delete')
def receive_before_update(mapper, connection, target):
    DS_CACHE.remove_value(target.cache_key)


__all__ = ['Datasource']
