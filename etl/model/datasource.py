# -*- coding: utf-8 -*-
"""Datasource model module."""
from sqlalchemy import *
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, Unicode, DateTime, LargeBinary
from sqlalchemy.orm import relationship, backref
from tw2.forms import TextField

from etl.lib.widgets import SmartWidgetTypes
from etl.model import DeclarativeBase
from etl.lib.dbsessions import session_factory

SESSIONS_CACHE = {}


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
    def dbsession(self):
        try:
            return SESSIONS_CACHE[self.uid]
        except KeyError:
            SESSIONS_CACHE[self.uid] = dbsession = session_factory(self.url)
            return dbsession


__all__ = ['Datasource']
