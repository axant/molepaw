# -*- coding: utf-8 -*-
from etl.tests.functional.controllers import BaseTestController
from etl.model import DBSession
from etl import model
from etl.controllers.editor import EditorController
from datetime import datetime, timedelta
import transaction


class TestEditorController(BaseTestController):
    controller = EditorController()

    def test_get_one(self):
        response = self.app.get(
            '/editor',
            params=dict(extraction=self.extraction),
            extra_environ=self.admin_env,
            status=200
        )
        assert 'Editing default_ext' in response.body.decode('utf-8')
        assert response.html.find(id='ExtractionVisualization_template') is not None
        assert response.html.find(id='DataSetsEditor_template') is not None
        assert response.html.find(id='StepsEditor_template') is not None

    def test_post(self):
        response = self.app.post_json(
            '/editor/' + str(self.extraction),
            {
                'visualization': {'type': 'histogram', 'axis': 'email_address,user_id'},
                'extraction': self.extraction
            },
            extra_environ=self.admin_env,
            status=200
        )

        assert response.json['extraction']['visualization'] == 'histogram'
        assert response.json['extraction']['graph_axis'] == 'email_address,user_id'

    def test_pipeline(self):
        response = self.app.get(
            '/editor/' + str(self.extraction) + '/test_pipeline',
            extra_environ=self.admin_env,
            status=200
        )

        extraction = DBSession.query(model.Extraction).get(self.extraction)

        assert response.json['results'][0]['columns'] == [
            'user_id', 'user_name', 'email_address',
            'display_name', 'password', 'created'
        ]
        assert response.json['results'][0]['data'] == [
            [
                '0', '1', 'admin', 'admin@somedomain.com', 'Example Admin',
                'fba0f3a1d7c6ca3afd2d60d68ca61412f20e770bce6ee7b...', '2018-09-11 17:04:42.240496'
            ],
            [
                '1', '2', 'manager', 'manager@somedomain.com', 'Example manager',
                'ec26c4986d76515189e5e40d1eefa60ad9b9d20ecad1297...', '2018-09-11 17:04:42.241971'
            ]
        ]
        assert response.json['results'][0]['errors'] is None
        assert len(extraction.steps) == len(response.json['results'])

    def test_save_category(self):
        extraction = DBSession.query(model.Extraction).get(self.extraction)
        assert extraction.category_id == self.category
        response = self.app.get(
            '/editor/' + str(self.extraction) + '/save_category',
            params=dict(category=-1),
            extra_environ=self.admin_env,
            status=302
        )
        extraction = DBSession.query(model.Extraction).get(self.extraction)
        assert extraction.category_id is None


class TestEditorControllerMongo(BaseTestController):
    controller = EditorController()
        
    def setUp(self):
        super(BaseTestController, self).setUp()
        self.m_datasource = self.create_datasource(name=u'datasource mongo', url=u'mongodb://localhost:27017/moletest')
        self.m_dataset_find = self.create_dataset(self.m_datasource, name=u'dataset mongo find',
                                                  query=u'''#collection=main_collection
{"data": {"$gt": 5}}''')
        self.m_dataset_aggregate = self.create_dataset(self.m_datasource, name=u'dataset mongo aggregate',
                                                query=u'''#collection=main_collection
[{"$match": {"data": {"$gt": 5}}}]''')
        self._db = self.m_datasource.dbsession._session.get_default_database()
        self._db.create_collection('main_collection')
        self._db.main_collection.insert_many([
            {"data": i, "data2": i + 100, "day": datetime.utcnow() + timedelta(days=i)} for i in range(105)
        ])
        self.ext1 = self.create_extraction(
            name='mongo_ext1',
        )
        self.extds1 = model.ExtractionDataSet(
            dataset_id=self.m_dataset_find.uid,
            extraction_id=self.ext1.uid
        )
        DBSession.add(self.m_datasource)
        DBSession.add(self.m_dataset_find)
        DBSession.add(self.m_dataset_aggregate)
        DBSession.add(self.ext1)
        DBSession.add(self.extds1)
        DBSession.flush()
        transaction.commit()

    def tearDown(self):
        super(BaseTestController, self).tearDown()
        self._db.drop_collection('main_collection')        

    def test_mongo_get_one(self):
        self.ext1 = DBSession.merge(self.ext1)
        response = self.app.get(
            '/editor',
            params=dict(extraction=self.ext1.uid),
            extra_environ=self.admin_env,
            status=200
        )
        assert 'Editing mongo_ext1' in response.body.decode('utf-8')
