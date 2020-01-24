from pandas import DataFrame
from etl.lib.dbsessions import session_factory
from webob.exc import HTTPPreconditionFailed
from nose.tools import assert_raises
from sqlalchemy.exc import OperationalError

class AbstractDBSessions(object):
    _url = None

    def get_session(self):
        return session_factory(self._url)

    def test_execute_query_users(self):
        result = self.get_session().execute(self._query_users)
        assert isinstance(result, DataFrame), type(result)
        assert len(result) == 1, result

    def test_execute_wrong_table(self):
        try:
            result = self.get_session().execute(self._query_wrong_table)
            assert False, 'should raise'
        except HTTPPreconditionFailed as e:
            assert "doesn't exist, check it" in str(e)
        except OperationalError as e:
            assert 'no such table: this_does_not_exists' in str(e)


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
        self._db = self.get_session()._session.get_default_database()
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
        result = self.get_session().execute(self._query_no_directive)
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
    _url = 'sqlite:///etl/tests/testdatasource.db'
    _query_users = 'SELECT * FROM tg_user WHERE user_name = \'admin\''
    _query_wrong_table = 'SELECT * FROM this_does_not_exists'
