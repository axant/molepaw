from etl.lib.dbsessions import session_factory
from etl.tests.functional.controllers import BaseTestController
from etl import model
from etl.model import DBSession
from tgext.pluggable import app_model
import transaction
from datetime import datetime, timedelta
from mock import Mock, patch
from random import randint


class TestChartVisualization(BaseTestController):
    _db = None
    url = 'mongodb://127.0.0.1:27017/moletest#fruits'
    fruits = ['Apples', 'Pears', 'Nectarines', 'Plums', 'Grapes', 'Strawberries']
    counts = [5, 3, 4, 2, 4, 6]
    deltas = [10, 20, 30, 40, 50, 60]

    def get_session(self):
        return session_factory(self.url)

    def setUp(self):
        # remember that whatever setUp fails, the tearDown is not called
        # and all following tests will fail
        # for example a connection ploblem with mongo
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
            extraction=extraction,
            uid=randint(1, 1000)
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
                extraction=entities['extraction_uid']
            ),
            extra_environ=self.admin_env,
            status=200
        )
        assert 'Fruits Extraction' in response.body.decode('utf-8')
        assert response.html.find(id='results-count').get_text() == '6'
        assert response.html.find(id='histogram-visualization') is not None

    def test_view_histogram_visualization_filter_required(self):
        self._db.fruits.insert_many({'name': n, 'value': v} for (n,v) in (('a', j) for j in range(10000)))
        entities = self.populate_for_chart_visualization('histogram', 'name,value')
        response = self.app.get(
            '/extractions/view',
            params=dict(
                extraction=entities['extraction_uid']
            ),
            extra_environ=self.admin_env,
            status=200
        )
        assert 'Fruits Extraction' in response.body.decode('utf-8')
        assert response.html.find(id='results-count').get_text() == '10006', response.html.find(id='results-count').get_text()
        assert response.html.find(id='histogram-visualization') is not None

    @patch('etl.lib.helpers.figure', Mock(side_effect=Exception('figure not figuring')))
    def test_view_histogram_visualization_exception(self):
        entities = self.populate_for_chart_visualization('histogram', 'name,value')
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
        # is None because of exception
        assert response.html.find(id='histogram-visualization') is None, response.html

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
        assert response.html.find(id='linechart-visualization') is not None, response.html

    def test_view_linechart_visualization_unsupported_index(self):
        entities = self.populate_for_chart_visualization('linechart', 'name,value')
        from etl.controllers.extractions import LINECHART_SUPPORTED_INDEXES
        del LINECHART_SUPPORTED_INDEXES[:]  # clear
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
        # None because of unsupported index
        assert response.html.find(id='linechart-visualization') is None


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

    def test_view_piechart_visualization_bicolor(self):
        entities = self.populate_for_chart_visualization('pie', 'name,value')
        self._db.fruits.remove({"value": {"$gt": 3}})
        response = self.app.get(
            '/extractions/view',
            params=dict(
                extraction=entities['extraction_uid']
            ),
            extra_environ=self.admin_env,
            status=200
        )
        assert 'Fruits Extraction' in response.body.decode('utf-8')
        assert response.html.find(id='results-count').get_text() == '2'
        assert response.html.find(id='pie-visualization') is not None
