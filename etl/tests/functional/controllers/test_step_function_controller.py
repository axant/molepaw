# -*- coding: utf-8 -*-
from etl.tests.functional.controllers import BaseTestController


class TestStepsFunctionController(BaseTestController):

    def test_get_one(self):
        response = self.app.get(
            '/editor/' + str(self.extraction) + '/function/get_one',
            dict(func='rename'),
            extra_environ=self.admin_env,
            status=200
        )

        assert response.json == {u'doc': u'Renames a column', u'name': u'rename'}

        self.app.get(
            '/editor/' + str(self.extraction) + '/function/get_one',
            dict(func='bad value'),
            extra_environ=self.admin_env,
            status=404
        )
