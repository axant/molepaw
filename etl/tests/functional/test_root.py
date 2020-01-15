# -*- coding: utf-8 -*-
"""
Functional test suite for the root controller.

This is an example of how functional tests can be written for controllers.

As opposed to a unit-test, which test a small unit of functionality,
functional tests exercise the whole application and its WSGI stack.

Please read http://pythonpaste.org/webtest/ for more information.

"""

from etl.tests import TestController


class TestRoot(TestController):
    def test_root_index(self):
        r = self.app.get('/', status=302, extra_environ=self.manager_env)
        assert 'http://localhost/extractions' == r.location, r.location
        r = r.follow(extra_environ=self.manager_env, status=200)
