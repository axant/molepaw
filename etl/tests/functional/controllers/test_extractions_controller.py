from etl.lib.dbsessions import session_factory
from etl.tests.functional.controllers import BaseTestController
from etl import model
from etl.model import DBSession
from mock import patch, Mock, PropertyMock
from tgext.pluggable import app_model
import transaction
from datetime import datetime, timedelta
from random import choice


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

    @patch('etl.controllers.extractions.request')
    def test_view_table_visualization_json_format(self, mockrequest):
        import json
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

    @patch('etl.controllers.extractions.request')
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


class TestChartVisualization(BaseTestController):
    _db = None
    url = 'mongodb://127.0.0.1:27017/moletest#fruits'
    fruits = ['Apples', 'Pears', 'Nectarines', 'Plums', 'Grapes', 'Strawberries']
    counts = [5, 3, 4, 2, 4, 6]
    deltas = [10, 20, 30, 40, 50, 60]

    def get_session(self):
        return session_factory(self.url)

    def setUp(self):
        super(TestChartVisualization, self).setUp()
        self._db = self.get_session()._session.get_default_database()
        self._db.create_collection('fruits')
        values = []
        for f, v, d in zip(self.fruits, self.counts, self.deltas):
            values.append({
                'name': f,
                'value': v,
                'day': datetime.utcnow() - timedelta(days=d)
            })
        self._db.fruits.insert_many(values)

    def tearDown(self):
        super(TestChartVisualization, self).tearDown()
        self._db.drop_collection('fruits')

    def populate_for_chart_visualization(self, visualization, axis):
        entities = {}
        datasource = self.create_datasource(
            name='fruits',
            url=self.url
        )
        DBSession.flush()
        entities['datasource_uid'] = datasource.uid
        cat = DBSession.query(app_model.Category).get(self.category)
        extraction = model.Extraction(
            name='Fruits Extraction',
            visualization=visualization,
            category=cat,
            graph_axis=axis
        )
        DBSession.add(extraction)
        DBSession.flush()
        entities['extraction_uid'] = extraction.uid
        dataset = self.create_dataset(
            datasource,
            name='All fruits',
            query='[{"$match": {"name": {"$ne": null}}}, {"$project": {"name": 1, "value": 1, "day": 1}}]'
        )
        DBSession.flush()
        entities['dataset_uid'] = dataset.uid
        extractiondataset = model.ExtractionDataSet(
            dataset=dataset,
            extraction=extraction
        )
        DBSession.add(extractiondataset)
        DBSession.flush()
        entities['extractiondataset_uid'] = extractiondataset.uid
        transaction.commit()
        return entities

    def test_view_histogram_visualization(self):
        entities = self.populate_for_chart_visualization('histogram', 'name,value')
        response = self.app.get(
            '/extractions/view',
            params=dict(
                extraction=entities['extractiondataset_uid']
            ),
            extra_environ=self.admin_env,
            status=200
        )
        assert 'Fruits Extraction' in response.body.decode('utf-8')
        assert response.html.find(id='results-count').get_text() == '6'
        assert response.html.find(id='histogram-visualization') is not None

    def test_view_linechart_visualization(self):
        entities = self.populate_for_chart_visualization('linechart', 'name,value')
        response = self.app.get(
            '/extractions/view',
            params=dict(
                extraction=entities['extraction_uid']
            ),
            extra_environ=self.admin_env,
            status=200
        )
        assert 'Fruits Extraction' in response.body.decode('utf-8')
        assert response.html.find(id='results-count').get_text() == '6'
        assert response.html.find(id='linechart-visualization') is not None

    def test_view_linechart_datetime_visualization(self):
        entities = self.populate_for_chart_visualization('linechart', 'day,value')
        response = self.app.get(
            '/extractions/view',
            params=dict(
                extraction=entities['extraction_uid']
            ),
            extra_environ=self.admin_env,
            status=200
        )
        assert 'Fruits Extraction' in response.body.decode('utf-8')
        assert response.html.find(id='results-count').get_text() == '6'
        assert response.html.find(id='linechart-visualization') is not None

    def test_view_piechart_visualization(self):
        entities = self.populate_for_chart_visualization('pie', 'name,value')
        response = self.app.get(
            '/extractions/view',
            params=dict(
                extraction=entities['extraction_uid']
            ),
            extra_environ=self.admin_env,
            status=200
        )

        assert 'Fruits Extraction' in response.body.decode('utf-8')
        assert response.html.find(id='results-count').get_text() == '6'
        assert response.html.find(id='pie-visualization') is not None




