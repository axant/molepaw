from etl.tests.functional.controllers import BaseTestController
from etl import model
from etl.model import DBSession
import transaction


class TestDashboardController(BaseTestController):

    def test_index(self):
        response = self.app.get(
            '/dashboard',
            extra_environ=self.admin_env
        )
        response.showbrowser()
        assert 8 == 9
