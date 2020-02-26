# -*- coding: utf-8 -*-
from etl.tests import TestController
from etl import model


class TestExtractions(TestController):
    def test_create(self):
        r = self.app.post(
            '/extractions/create',
            params={'name': 'first extraction'},
            status=302,
            extra_environ=self.manager_env,
        )
        assert 'http://localhost/extractions/index' == r.location, r.location
        r = r.follow(extra_environ=self.manager_env, status=200)
        assert 'first extraction' in r.text, r.text
        assert 'New Extraction successfully created' in r.text, r.text

    def test_view(self):
        extraction = self.create_extraction(name='extraction one')
        self.flush()
        extraction = model.DBSession.merge(extraction)
        r = self.app.get(
            '/extractions/view/%s' % extraction.uid,
            extra_environ=self.manager_env,
            status=200,
        )
        assert 'extraction one' in r.text, r.text
