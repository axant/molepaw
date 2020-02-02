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

    def test_error_xhr(self):
        r = self.app.get('/error/test?detail=sfiga', status=500, extra_environ=self.manager_env, xhr=True)
        assert '''<!DOCTYPE html>
<div style="width: 100%;">
    
      <h3>Error 500</h3>


  <div style="max-width: 100%;">sfiga</div>
    
</div>''' == r.body

    def test_error_xhr_no_detail(self):
        r = self.app.get('/error/test', status=500, extra_environ=self.manager_env, xhr=True)
        assert '''<!DOCTYPE html>
<div style="width: 100%;">
    
      <h3>Error 500</h3>


  <div style="max-width: 100%;"><p>We're sorry but we weren't able to process  this request.</p></div>
    
</div>''' == r.body, r.body
