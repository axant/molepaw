# -*- coding: utf-8 -*-
from etl.tests.functional.controllers import BaseTestController
from etl.model import DBSession
from etl import model
from beaker.cache import Cache, CacheManager
from mock import patch, Mock
import json


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
        flt = DBSession.query(model.ExtractionFilter).get(self.filter)
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
        flt = DBSession.query(model.ExtractionFilter).get(self.filter)
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

    @patch('etl.model.dataset.tg.cache', spec=CacheManager)
    def test_filter_perform(self, mockcache):
        mockcache.get_cache = Mock(return_value=Cache('TEST'))

        flt = model.DBSession.query(model.ExtractionFilter).get(self.filter)

        df = flt.perform()
        extraction_df = flt.extraction.perform()

        for column in df.columns:
            for i in range(0, len(df[column]) - 1):
                assert df[column][i] == extraction_df[column][i]

    def test_filters_from_template(self):
        r = self.app.get(
            '/extractions/filter/filters_from_template',
            {
                'extraction': self.extraction,
                'template': 'alphabetical',
                'field': 'email_address',
            },
            extra_environ=self.admin_env,
            status=200,
        )
        assert r.json['error'] is None, r.json
        assert DBSession.query(model.ExtractionFilter).count() != 1
        assert DBSession.query(model.ExtractionFilter).all()[1].name == u'A'
        assert DBSession.query(model.ExtractionFilter).all()[-3].name == u'Z'
        assert DBSession.query(model.ExtractionFilter).all()[-2].name == u'Symbols'
        assert DBSession.query(model.ExtractionFilter).all()[-1].name == u'0-9'
        assert DBSession.query(model.ExtractionFilter).all()[-1].steps[0].function == u'query'
        assert 'email_address' in json.loads(DBSession.query(model.ExtractionFilter).all()[-1].steps[0].options)['expression']

    def test_filters_from_template_validation_error(self):
        r = self.app.get(
            '/extractions/filter/filters_from_template',
            {
                'extraction': self.extraction,
                'template': 'alpha',
                'field': 'email_address',
            },
            extra_environ=self.admin_env,
            status=200,
        )
        assert r.json['error']['template'] == 'unknown template: alpha', r.json
        assert DBSession.query(model.ExtractionFilter).count() == 1

