# -*- coding: utf-8 -*-
from etl.tests import TestController
from etl.lib.dbsessions import MongoDBSession
from mongomock.mongo_client import MongoClient
from mock import patch, Mock
from nose.tools import assert_raises
from tg.exceptions import HTTPPreconditionFailed
import json
from pandas import DataFrame
from tg.util.webtest import test_context


class TestMongoDBSession(TestController):

    @patch('pymongo.MongoClient', Mock(side_effect=MongoClient))
    def setUp(self):
        super(TestMongoDBSession, self).setUp()
        self.mongo_session = MongoDBSession('mongodb://localhost:27017/test_db')
        self.mongo_session._session.get_default_database().create_collection('accounts')
        self.right_query = '''#collection=accounts
[{"$match": {"roles": ["USER"]}}, {"$project": {"roles": 1, "token": 1, "password": 1}}]'''
        self.dict_query = '''#collection=accounts
{"roles": ["USER"]}'''
        self.wrong_query_collection = '''#__collection=accounts
[{"$match": {"roles": ["USER"]}}, {"$project": {"roles": 1, "token": 1, "password": 1}}]'''
        self.wrong_query_json = '''#collection=accounts
[{"$match": {'roles': ["USER"]}}, {"$project": {"roles": 1, "token": 1, "password": 1}}]'''
        self.data = '''[
    {"password" : "pass1","roles" : ["USER", "UNRESTRICTED"], "age" : 675, "token" : ""},
    {"password" : "pass2","roles" : ["USER"], "age" : 806,"token" : ""},
    {"password" : "pass3","roles" : ["USER"], "age" : 0, "token" : "9ecf82c7e7ba11dbfea20cb84773339aff4d5f79"}
]'''

    def test_set_collection(self):
        assert self.mongo_session._collection is None
        self.mongo_session.set_collection('accounts')
        assert self.mongo_session._collection is not None
        assert_raises(
            HTTPPreconditionFailed,
            self.mongo_session.set_collection,
            'wrong_collection'
        )

    def test_execute_ok(self):
        self.mongo_session.set_collection('accounts')
        self.mongo_session._collection.insert_many(json.loads(self.data))
        df = self.mongo_session.execute(self.right_query)
        assert len(df) == 2
        assert isinstance(df, DataFrame)
        assert df['password'][0] == 'pass2'
        df = self.mongo_session.execute(self.dict_query)
        assert len(df) == 2
        assert isinstance(df, DataFrame)
        assert df['password'][0] == 'pass2'

    def test_execute_error(self):
        with test_context(self.app):
            assert_raises(
                HTTPPreconditionFailed,
                self.mongo_session.execute,
                self.wrong_query_collection
            )
            assert_raises(
                HTTPPreconditionFailed,
                self.mongo_session.execute,
                self.wrong_query_json
            )
