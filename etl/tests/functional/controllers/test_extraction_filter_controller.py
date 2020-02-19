# -*- coding: utf-8 -*-
from etl.tests.functional.controllers import BaseTestController
from etl.model import DBSession
from etl import model


class TestExtractionFilterController(BaseTestController):

    def test_post(self):
        response = self.app.post_json(
            '/extractions/filter/post',
            {'filter': self.filter_data, 'extraction': self.extraction},
            extra_environ=self.admin_env,
            status=200
        )
        assert response.json == {
            u'filter': {
                u'extraction_id': self.extraction,
                u'name': u'custom_flt',
                u'default': True,
                u'steps': [{u'function': u'query', u'extraction_id': None, u'uid': 2, u'enabled': True, u'priority': 0, u'function_doc': u"""Filters the rows for those matching the given expression.

    - Use "value != value" to get only rows where value is NaN
    - Use "value == value" to get only rows where value is not NaN

    Special values:

    * @utcnow -> current date and time in UTC
    * @nan -> NaN
    * @null -> None
    """, u'options': {u'expression': u"user_name != 'viewer'"}}], u'query': u"user_name != 'viewer'", u'uid': 2}}

    def test_delete(self):
        response = self.app.get(
            '/extractions/filter/delete',
            params={'uid': self.filter},
            extra_environ=self.admin_env,
            status=302
        )
        redirection = response.follow(
            extra_environ=self.admin_env
        )

        assert 'default_ext' in redirection.body.decode('utf-8')
        assert len(list(DBSession.query(model.ExtractionFilter).all())) == 0

    def test_delete_wrong_filter(self):
        self.app.get(
            '/extractions/filter/delete',
            params={'uid': 100},
            extra_environ=self.admin_env,
            status=404
        )

    def test_put(self):
        self.filter_data.update({
            'uid': 1,
            'steps': [{'uid': self.step}]
        })
        self.app.put_json(
            '/extractions/filter/put.json',
            {'filter': self.filter_data, 'extraction': self.extraction},
            extra_environ=self.admin_env
        )
        flt = DBSession.query(model.ExtractionFilter).get(1)
        assert flt.name == 'custom_flt'

    def test_put_no_default(self):
        self.filter_data.update({
            'uid': 1,
            'steps': [{'uid': self.step}]
        })
        del self.filter_data['default']
        self.app.put_json(
            '/extractions/filter/put.json',
            {'filter': self.filter_data, 'extraction': self.extraction},
            extra_environ=self.admin_env
        )
        flt = DBSession.query(model.ExtractionFilter).get(1)
        assert flt.name == 'custom_flt'    

    def test_put_404s(self):
        self.filter_data.update({
            'uid': 1000
        })
        # bad extraction_filter
        self.app.put_json(
            '/extractions/filter/put.json',
            {'filter': self.filter_data, 'extraction': self.extraction},
            extra_environ=self.admin_env,
            status=404
        )
        # bad extraction_filter step0
        self.app.put_json(
            '/extractions/filter/put.json',
            {'filter': {
                'uid': 1,
                'steps': [{'uid': 2000}]
            }, 'extraction': self.extraction},
            extra_environ=self.admin_env,
            status=404
        )
