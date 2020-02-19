# -*- coding: utf-8 -*-
from etl.tests.functional.controllers import BaseTestController
from etl.model import DBSession
from etl import model
from etl.controllers.editor import EditorController


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


