# -*- coding: utf-8 -*-
"""The application's model objects"""

from zope.sqlalchemy import register
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Global session manager: DBSession() returns the Thread-local
# session object appropriate for the current web request.
maker = sessionmaker(autoflush=True, autocommit=False)
DBSession = scoped_session(maker)
register(DBSession)


# Base class for all of our model classes: By default, the data model is
# defined with SQLAlchemy's declarative extension, but if you need more
# control, you can switch to the traditional method.
DeclarativeBase = declarative_base()

# There are two convenient ways for you to spare some typing.
# You can have a query property on all your model classes by doing this:
# DeclarativeBase.query = DBSession.query_property()
# Or you can use a session-aware mapper as it was used in TurboGears 1:
# DeclarativeBase = declarative_base(mapper=DBSession.mapper)

# Global metadata.
# The default metadata is the one from the declarative base.
metadata = DeclarativeBase.metadata

# If you have multiple databases with overlapping table names, you'll need a
# metadata for each database. Feel free to rename 'metadata2'.
# from sqlalchemy import MetaData
# metadata2 = MetaData()

#####
# Generally you will not want to define your table's mappers, and data objects
# here in __init__ but will want to create modules them in the model directory
# and import them at the bottom of this file.
######


def init_model(engine):
    """Call me before using any of the tables or classes in the model."""
    DBSession.configure(bind=engine)


# Import your model modules here.
from etl.model.auth import User, Group, Permission
from .dataset import DataSet
from .datasource import Datasource
from .extraction import Extraction, ExtractionDataSet
from .extractionstep import ExtractionStep
from .extraction_filter import ExtractionFilter
from .dashboard import Dashboard, DashboardExtractionAssociation

__all__ = ('User', 'Group', 'Permission', 'DataSet', 'Datasource',
           'Extraction', 'ExtractionDataSet', 'ExtractionStep', 'ExtractionFilter',
           'Dashboard', 'DashboardExtractionAssociation')
