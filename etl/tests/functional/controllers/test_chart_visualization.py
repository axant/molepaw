from etl.lib.dbsessions import session_factory
from etl.tests.functional.controllers import BaseTestController
from etl import model
from etl.model import DBSession
from tgext.pluggable import app_model
import transaction
from datetime import datetime, timedelta


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
