# -*- coding: utf-8 -*-
from pandas import DataFrame


class SQLAlchemyDBSession(object):
    def __init__(self, url):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import scoped_session, sessionmaker

        self._session = scoped_session(sessionmaker(autoflush=False, autocommit=False))
        self._session.configure(bind=create_engine(url, pool_recycle=300))

    def execute(self, q, limit=None):
        result = self._session.execute(q)
        if limit is None:
            df = DataFrame(result.fetchall())
        else:
            df = DataFrame(result.fetchmany(limit))
        df.columns = list(result.keys())
        self._session.remove()
        return df

    def rollback(self):
        self._session.rollback()
        self._session.remove()
