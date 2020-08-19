# -*- coding: utf-8 -*-
"""Unit test suite for the models of the application."""

from nose.tools import eq_
from etl.model import DBSession
from etl.tests import load_app
from etl.tests import setup_db, teardown_db

__all__ = ['ModelTest']


def setup():
    """Setup test fixture for all model tests."""
    load_app()
    setup_db()


def teardown():
    """Tear down test fixture for all model tests."""
    teardown_db()


class ModelTest(object):
    """Base unit test case for the models."""

    klass = None
    attrs = {}

    def setUp(self):
        """Setup test fixture for each model test method."""
        try:
            new_attrs = {}
            new_attrs.update(self.attrs)
            new_attrs.update(self.do_get_dependencies())
            self.obj = self.klass(**new_attrs)
            for k, v in self.after_creation().items():  # usually klass does not have update method
                setattr(self.obj, k, v)
            DBSession.add(self.obj)
            DBSession.flush()
            return self.obj
        except:
            DBSession.rollback()
            raise

    def tearDown(self):
        """Tear down test fixture for each model test method."""
        DBSession.rollback()

    def do_get_dependencies(self):
        """Get model test dependencies.

        Use this method to pull in other objects that need to be created
        for this object to be build properly.

        """
        return {}

    def after_creation(self):
        """use this when you would need self.obj in do_get_dependecies"""
        return {}
        
    def test_create_obj(self):
        """Model objects can be created"""
        pass

    def test_query_obj(self):
        """Model objects can be queried"""
        obj = DBSession.query(self.klass).one()
        for key, value in self.attrs.items():
            eq_(getattr(obj, key), value)

    def test_repr_obj(self):
        assert repr(self.obj).startswith('<') and self.klass.__name__ in repr(self.obj), self.obj
