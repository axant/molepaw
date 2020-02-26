from etl.tests.functional.controllers import BaseTestController
from etl import model
from etl.model import DBSession
from mock import patch, Mock, PropertyMock
from tg.request_local import Request
import json


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

    def test_reload_data(self):
        response = self.app.get(
            '/extractions/reload_data/' + str(self.extraction),
            extra_environ=self.admin_env,
            status=302
        )
        redirection = response.follow(
            extra_environ=self.admin_env
        )
        assert 'Data reloaded' in redirection.body.decode('utf-8')

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
        # it's the same as precedent becouse the filter is marked as default
        # so event if it's not specified it's applied
        response = self.app.get(
            '/extractions/view',
            params=dict(
                extraction=self.extraction
            ),
            extra_environ=self.admin_env,
            status=200
        )
        assert 'admin@somedomain.com' in response.body.decode('utf-8')
        assert 'manager@somedomain.com' in response.body.decode('utf-8')
        assert 'editor@somedomain.com' not in response.body.decode('utf-8')

    @patch('etl.controllers.extractions.request', spec=Request)
    def test_view_table_visualization_json_format(self, mockrequest):
        type(mockrequest).response_type = PropertyMock(return_value='application/json')
        response = self.app.get(
            '/extractions/view',
            params=dict(
                extraction=self.extraction,
                extraction_filter=self.filter
            ),
            extra_environ=self.admin_env,
            status=200
        )
        assert 'admin@somedomain.com' in response.text
        assert 'manager@somedomain.com' in response.text
        assert 'editor@somedomain.com' not in response.text
        try:
            json.loads(response.text)
            assert True
        except ValueError:
            assert False

    @patch('etl.controllers.extractions.request', spec=Request)
    def test_view_table_visualization_csv_format(self, mockrequest):
        import csv
        type(mockrequest).response_type = PropertyMock(return_value='text/csv')
        response = self.app.get(
            '/extractions/view',
            params=dict(
                extraction=self.extraction,
                extraction_filter=self.filter
            ),
            extra_environ=self.admin_env,
            status=200
        )
        assert 'admin@somedomain.com' in response.text
        assert 'manager@somedomain.com' in response.text
        assert 'editor@somedomain.com' not in response.text
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(response.text)
            assert dialect.quotechar == u'"'
            assert dialect.delimiter == u','
        except Exception:
            assert False

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
        assert response.html.find(id='results-count').get_text() == '0'

    def test_view_wrong_filter_error(self):
        response = self.app.get(
            '/extractions/view',
            params=dict(
                extraction=self.extraction,
                extraction_filter=3000
            ),
            extra_environ=self.admin_env,
            status=200
        )
        assert 'ERROR RETRIEVING DATA: The resource could not be found.' in response.body.decode('utf-8')

    def tests_extraction_dataset_descr(self):
        ext_dataset = DBSession.query(model.ExtractionDataSet)\
            .get(self.extractiondataset)

        assert ext_dataset.descr == 'default_dts left join'
