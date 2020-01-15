# -*- coding: utf-8 -*-
from .http_json import HTTPJSONSession
from .sqla import SQLAlchemyDBSession
from .mongodb import MongoDBSession
from .http_csv import HTTPCSVSession

def session_factory(url):
    for schema in DBSESSION_SCHEMAS:
        if url.startswith(schema):
            return DBSESSION_SCHEMAS[schema](url)
    else:
        raise KeyError('Unable to find a supported engine for {}'.format(url))


DBSESSION_SCHEMAS = {
    'mysql': SQLAlchemyDBSession,
    'mongo': MongoDBSession,
    # can be used only for tests as sqlite doesn't support concurrent operations
    'sqlite': SQLAlchemyDBSession,
    'csv': HTTPCSVSession,
    'json': HTTPJSONSession
}
