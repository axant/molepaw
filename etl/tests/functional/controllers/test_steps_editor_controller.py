# -*- coding: utf-8 -*-
from etl.tests.functional.controllers import BaseTestController
from etl import model
from etl.model import DBSession
import json


class TestStepsEditorController(BaseTestController):

    def test_get_all(self):
        response = self.app.get(
            '/editor/' + str(self.extraction) + '/steps',
            extra_environ=self.admin_env,
            status=200
        )
        assert response.json == {u'steps': [{u'function': u'query', u'extraction_id': 1, u'uid': 1, u'enabled': True, u'priority': 0, u'function_doc': u"""Filters the rows for those matching the given expression.

    - Use "value != value" to get only rows where value is NaN
    - Use "value == value" to get only rows where value is not NaN

    Special values:

    * @utcnow -> current date and time in UTC
    * @nan -> NaN
    * @null -> None
    """, u'options': {u'expression': u"user_name != 'viewer'"}}]}

    def test_put(self):
        response = self.app.put_json(
            '/editor/' + str(self.extraction) + '/steps/put',
            dict(
                uid=self.step,
                function='query',
                priority=0,
                options={u"expression": u"user_name = 'viewer'"}
            ),
            extra_environ=self.admin_env,
            status=200
        )
        step = DBSession.query(model.ExtractionStep).get(self.step)

        assert response.json['step']['function'] == 'query'
        assert response.json['step']['priority'] == 0
        assert response.json['step']['options'] == {u"expression": u"user_name = 'viewer'"}
        assert response.json['step']['function'] == step.function
        assert response.json['step']['priority'] == step.priority
        assert response.json['step']['options'] == json.loads(step.options)

    def test_put_error(self):
        self.app.put_json(
            '/editor/' + str(self.extraction) + '/steps/put',
            dict(
                uid=self.step,
                function='query',
                priority=0,
                options="query sbagliata in partenza"
            ),
            extra_environ=self.admin_env,
            status=412
        )

    def test_post(self):
        response = self.app.post_json(
            '/editor/' + str(self.extraction) + '/steps/post',
            dict(function='query', priority=1, options={u"expression": u"and email_address <> null"}),
            extra_environ=self.admin_env,
            status=200
        )

        assert response.json == dict()
        assert DBSession.query(model.ExtractionStep).filter(
            model.ExtractionStep.options == json.dumps({u"expression": u"and email_address <> null"}),
            model.ExtractionStep.function == 'query',
            model.ExtractionStep.extraction_id == self.extraction
        ).first() is not None

    def test_post_error(self):
        self.app.post_json(
            '/editor/' + str(self.extraction) + '/steps/post',
            dict(function='query', priority=1, options=None),
            extra_environ=self.admin_env,
            status=412
        )

    def tests_delete(self):
        response = self.app.get(
            '/editor/' + str(self.extraction) + '/steps/delete',
            dict(uid=self.step),
            extra_environ=self.admin_env,
            status=200
        )

        assert response.json == dict()
        assert DBSession.query(model.ExtractionStep).get(self.step) is None

    def test_toggle(self):
        value = 1 if not DBSession.query(model.ExtractionStep).get(self.step).enabled else 0
        response = self.app.get(
            '/editor/' + str(self.extraction) + '/steps/toggle',
            dict(uid=self.step, enabled=value),
            extra_environ=self.admin_env,
            status=200
        )
        assert response.json == dict()
        assert DBSession.query(model.ExtractionStep).get(self.step).enabled is not value
