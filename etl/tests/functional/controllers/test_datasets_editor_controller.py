# -*- coding: utf-8 -*-
from etl import model
from etl.model import DBSession
from etl.tests.functional.controllers import BaseTestController
import transaction
from mock import patch, Mock, PropertyMock


class TestDatasetsEditorController(BaseTestController):

    def test_get_all(self):
        response = self.app.get(
            '/editor/' + str(self.extraction) + '/datasets',
            extra_environ=self.admin_env,
            status=200
        )

        assert response.json[u"datasets"] == [{
            u"extraction_id": self.extraction,
            u"join_other_col": None,
            u"join_self_col": None,
            u"name": u"default_dts",
            u"join_type": u"left",
            u"priority": 0,
            u"datasource": u"default_ds",
            u"dataset_id": self.dataset,
            u"uid": 1
        }]
        assert response.json[u'sampledata'][u'errors'] is None
        assert response.json[u'sampledata'][u'columns'] == [
            u"user_id", u"user_name", u"email_address", u"display_name", u"password", u"created"
        ]

    @patch('etl.model.extraction.Extraction.fetch', Mock(side_effect=Exception()))
    def test_get_all_error(self):
        response = self.app.get(
            '/editor/' + str(self.extraction) + '/datasets',
            extra_environ=self.admin_env,
            status=200
        )
        assert response.json[u"datasets"] == [{
            u"extraction_id": self.extraction,
            u"join_other_col": None,
            u"join_self_col": None,
            u"name": u"default_dts",
            u"join_type": u"left",
            u"priority": 0,
            u"datasource": u"default_ds",
            u"dataset_id": self.dataset,
            u"uid": 1
        }]
        assert response.json[u'sampledata'][u'errors'] is not None
        assert response.json[u'sampledata'][u'columns'] == []
        assert response.json[u'sampledata'][u'data'] == []

    def add_dataset(self, query, name):
        group_ds = self.create_datasource(
            name=name
        )
        DBSession.flush()

        group_ds_uid = group_ds.uid
        group_dt = self.create_dataset(
            group_ds,
            name='Group dataset',
            query=query
        )
        DBSession.flush()
        group_dt_uid = group_dt.uid
        transaction.commit()
        return {
            'group_dt_uid': group_dt_uid,
            'group_ds_uid': group_ds_uid
        }

    def test_post(self):
        entities = self.add_dataset(
            'SELECT g.group_id, g.group_name, g.display_name, g.created, m.user_id FROM tg_group g JOIN tg_user_group m ON g.group_id=m.group_id',
            'Group datasource'
        )
        response = self.app.post_json(
            '/editor/' + str(self.extraction) + '/datasets/post',
            dict(
                datasetid=entities['group_dt_uid'],
                join_type='left',
                join_self_col='user_id',
                join_other_col='user_id'
            ),
            extra_environ=self.admin_env,
            status=200
        )

        assert response.json == dict()
        assert DBSession.query(model.ExtractionDataSet).filter(
            model.ExtractionDataSet.extraction_id == self.extraction,
            model.ExtractionDataSet.dataset_id == entities['group_dt_uid'],
            model.ExtractionDataSet.join_type == 'left',
            model.ExtractionDataSet.join_self_col == 'user_id',
            model.ExtractionDataSet.join_other_col == 'user_id'
        ).first() is not None

    def test_put(self):
        entities = self.add_dataset(
            'SELECT g.group_id, g.group_name, g.display_name, g.created, m.user_id FROM tg_group g JOIN tg_user_group m ON g.group_id=m.group_id',
            'Group datasource'
        )
        response = self.app.post_json(
            '/editor/' + str(self.extraction) + '/datasets/post',
            dict(
                datasetid=entities['group_dt_uid'],
                join_type='left',
                join_self_col='user_id',
                join_other_col='user_id'
            ),
            extra_environ=self.admin_env,
            status=200
        )
        extdts_uid = DBSession.query(model.ExtractionDataSet).filter(
            model.ExtractionDataSet.extraction_id == self.extraction,
            model.ExtractionDataSet.dataset_id == entities['group_dt_uid'],
            model.ExtractionDataSet.join_type == 'left',
            model.ExtractionDataSet.join_self_col == 'user_id',
            model.ExtractionDataSet.join_other_col == 'user_id'
        ).first().uid

        response = self.app.put_json(
            '/editor/' + str(self.extraction) + '/datasets/put',
            dict(
                uid=extdts_uid,
                datasetid=entities['group_dt_uid'],
                join_type='inner',
                join_self_col='user_id',
                join_other_col='user_id'
            ),
            extra_environ=self.admin_env,
            status=200
        )

        assert response.json == dict(
            join_type='inner',
            join_self_col='user_id',
            join_other_col='user_id'
        )

    def test_delete(self):
        response = self.app.get(
            '/editor/' + str(self.extraction) + '/datasets/delete',
            params=dict(uid=self.extractiondataset),
            extra_environ=self.admin_env,
            status=200
        )
        assert response.json == dict()
        assert DBSession.query(model.ExtractionDataSet).get(self.extractiondataset) is None

