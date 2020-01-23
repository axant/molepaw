from pandas import DataFrame
from etl.lib.dbsessions import session_factory, DBSESSION_SCHEMAS
from etl.lib.dbsessions.sqla import SQLAlchemyDBSession
from etl.lib.dbsessions.mongodb import MongoDBSession
from etl.lib.dbsessions.http_csv import HTTPCSVSession
from etl.lib.dbsessions.http_json import HTTPJSONSession
from webob.exc import HTTPPreconditionFailed
from nose.tools import assert_raises


class AbstractDBSessions(object):
    _session = None
    _db = None
    _url = None
    _query = None

    def test_execute_query_users(self):
        result = self._session.execute(self._query_users)
        assert isinstance(result, DataFrame), type(result)
        assert len(result) == 1, result

    def test_execute_wrong_table(self):
        try:
            result = self._session.execute(self._query_wrong_table)
            assert False, 'should raise'
        except HTTPPreconditionFailed as e:
            assert "doesn't exist, check it" in str(e)


class TestMongoDBSession(AbstractDBSessions):
    _url = 'mongodb://127.0.0.1:27017/moletest#other_users'
    _query_users = '''
#collection=tg_user
{"user_name" : "admin"}'''
    _query_wrong_table = '''
#collection=this_does_not_exists
{"user_name" : "admin"}'''
    _query_no_directive = '[{"$match": {"user_name" : "admin"}}, {"$project": {"age": 1}}]'

    def setUp(self):
        self._session = session_factory(self._url)
        self._db = self._session._session.get_default_database()
        self._db.create_collection('tg_user')
        self._db.create_collection('other_users')
        self._db.tg_user.insert_many([
            {"user_name": "admin",  "age" : 675, "token" : ""},
            {"user_name": "editor", "age" : 806,"token" : ""},
            {"user_name": "guest", "age" : 0, "token" : "9ecf82c7e7ba11dbfea20cb84773339aff4d5f79"}
        ])
        self._db.other_users.insert_many([
            {"user_name": "admin", "age": 675, "token": ""},
            {"user_name": "editor", "age": 806, "token": ""},
            {"user_name": "guest", "age": 0, "token": "9ecf82c7e7ba11dbfea20cb84773339aff4d5f79"}
        ])

    def tearDown(self):
        self._db.drop_collection('tg_user')
        self._db.drop_collection('other_users')

    def test_execute_aggregation_no_directive(self):
        result = self._session.execute(self._query_no_directive)
        assert isinstance(result, DataFrame)
        assert result['age'][0] == 675

    def test_errors(self):
        _session = session_factory('mongodb://127.0.0.1:27017/moletest')
        assert_raises(
            HTTPPreconditionFailed,
            _session.execute,
            self._query_no_directive
        )
        query = '''
            #collection=tg_user
            {'user_name' : "admin"}'''
        assert_raises(
            HTTPPreconditionFailed,
            _session.execute,
            query
        )


class TestSQLite3DBSession(AbstractDBSessions):
    _url = 'sqlite:///moletest'
    _query_users = 'SELECT * FROM tg_user'
    _query_wrong_table = 'SELECT * FROM this_does_not_exists'
    
    def setUp(self):
        self._session = session_factory(self._url)
        self._db = self._session._session
        self._db.execute('CREATE TABLE tg_user (user_name VARCHAR PRIMARY KEY, age INTEGER')
        self._db.execute('''
INSERT INTO tg_user (user_name, age)
VALUES
(admin, 675), 
(editor, 806),
(guest, 0)''')

    def tearDown(self):
        self._db.execute('DROP TABLE tg_user')
