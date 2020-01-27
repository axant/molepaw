from etl.tests.functional.controllers import BaseTestController
from etl import model
from etl.model import DBSession
from mock import patch, Mock
from nose.tools import assert_raises


class TestExtractionsController(BaseTestController):

    def test_index(self):
        response = self.app.get(
            '/extractions',
            extra_environ=self.admin_env
        )
        # existing categories and extractions are displayed
        assert 'Default category 1' in response.body.decode('utf-8')
        assert 'default_ext' in response.body.decode('utf-8')
        assert 'No Category' in response.body.decode('utf-8')

    def test_create(self):
        response = self.app.get(
            '/extractions',
            extra_environ=self.admin_env
        )
        form = response.form
        form['name'] = 'Created extraction'

        submission = form.submit(
            extra_environ=self.admin_env,
            status=302
        )
        redirection = submission.follow(
            extra_environ=self.admin_env,
            status=200
        )

        assert 'Created extraction' in redirection.body.decode('utf-8')
        assert 'New Extraction successfully created' in redirection.body.decode('utf-8')

    def test_delete(self):
        response = self.app.get(
            '/extractions/delete',
            params=dict(uid=self.extraction),
            extra_environ=self.admin_env,
            status=302
        )
        redirection = response.follow(
            extra_environ=self.admin_env
        )
        assert DBSession.query(model.Extraction).get(self.extraction) is None
        assert 'Extraction correctly deleted' in redirection.body.decode('utf-8')

    def test_view_table_visualization(self):
        response = self.app.get(
            '/extractions/view',
            params=dict(
                extraction=self.extraction,
                extraction_filter=self.filter
            ),
            extra_environ=self.admin_env,
            status=200
        )

        assert 'admin@somedomain.com' in response.body.decode('utf-8')
        assert 'manager@somedomain.com' in response.body.decode('utf-8')
        assert 'editor@somedomain.com' not in response.body.decode('utf-8')

    @patch('etl.model.extraction.Extraction.perform', Mock(side_effect=ValueError()))
    def test_view_extraction_error(self):
        response = self.app.get(
            '/extractions/view',
            params=dict(
                extraction=self.extraction
            ),
            extra_environ=self.admin_env,
            status=302
        )

        assert 'The resource was found at http://localhost/error; you should be redirected automatically.'\
            in response.body.decode('utf-8')
        redirection = response.follow(
            extra_environ=self.admin_env,
            status=404
        )

        assert 'ERROR RETRIEVING DATA:' in redirection.body.decode('utf-8')

    @patch('etl.model.extraction_filter.ExtractionFilter.perform', Mock(side_effect=ValueError()))
    def test_view_filter_error(self):
        response = self.app.get(
            '/extractions/view',
            params=dict(
                extraction=self.extraction,
                extraction_filter=self.filter
            ),
            extra_environ=self.admin_env,
            status=200
        )

        assert 'ERROR RETRIEVING DATA:' in response.body.decode('utf-8')
        assert '0 Results' in response.body.decode('utf-8')
