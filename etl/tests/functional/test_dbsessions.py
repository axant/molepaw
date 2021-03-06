from pandas import DataFrame
from etl.lib.dbsessions import session_factory
from etl.tests import TestController
from etl import model
from webob.exc import HTTPPreconditionFailed
from nose.tools import assert_raises
from sqlalchemy.exc import OperationalError
from mock import patch, Mock


class AbstractDBSessions(object):
    _url = None
    _query_users = None
    _query_wrong_table = None

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
        except OperationalError as e:
            assert 'no such table: this_does_not_exists' in str(e)
        except ValueError as e:
            assert "The content is presented as 'text/plain' while 'text/csv' was expected" in str(e)\
                or "The content is presented as 'text/plain' while 'application/json' was expected" in str(e)\
                or "collection this_does_not_exists does not exists" in str(e), str(e)

    def test_rollback(self):
        self.get_session().rollback()


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
            {"user_name": "admin",  "age": 675, "token": ""},
            {"user_name": "editor", "age": 806, "token": ""},
            {"user_name": "guest", "age": 0, "token": "9ecf82c7e7ba11dbfea20cb84773339aff4d5f79"}
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

    def test_execute_aggregation_with_limit(self):
        result = self.get_session().execute('''#collection=tg_user
[{"$match": {"age" : {"$gt": 0}}}, {"$project": {"age": 1}}, {"$limit": 1}]''', limit=100)
        assert isinstance(result, DataFrame)
        assert result['age'][0] == 675
        # limit=100 will override the limit 1
        assert len(result) == 2, len(result)

    def test_execute_aggregation_with_execute_limit(self):
        result = self.get_session().execute('''#collection=tg_user
[{"$match": {"age" : {"$gt": 0}}}, {"$project": {"age": 1}}]''', limit=1)
        assert isinstance(result, DataFrame)
        assert result['age'][0] == 675
        assert len(result) == 1, len(result)

    def test_execute_find_with_limit(self):
        result = self.get_session().execute('''#collection=tg_user
{"age": {"$gt": 0}}''', limit=1)
        assert isinstance(result, DataFrame)
        assert result['age'][0] == 675
        assert len(result) == 1, len(result)

    def test_errors(self):
        _session = session_factory('mongodb://127.0.0.1:27017/moletest')
        # both url and query don't contain the collection so the session
        # doesn't know where to execute the query
        with assert_raises(ValueError) as ar:
            _session.execute(self._query_no_directive)
        assert str(ar.exception) == 'no collection specified'
        # query is not valid json
        with assert_raises(ValueError) as ar:
            _session.execute('''
            #collection=tg_user
            {'user_name' : "admin"}''')
        assert str(ar.exception) in (
            'Expecting property name: line 1 column 2 (char 1)',  # py2
            'Expecting property name enclosed in double quotes: line 1 column 2 (char 1)'  # py3
        ), str(ar.exception)


class TestSQLite3DBSession(AbstractDBSessions):
    _url = 'sqlite:///etl/tests/testdatasource.db'
    _query_users = 'SELECT * FROM tg_user WHERE user_name = \'admin\''
    _query_wrong_table = 'SELECT * FROM this_does_not_exists'

    def test_execute_with_limit(self):
        result = self.get_session().execute('select * from tg_user', limit=1)
        assert isinstance(result, DataFrame)
        assert result['user_name'][0] == 'admin'
        assert len(result) == 1, len(result)        


class TestCsvDBSession(AbstractDBSessions, TestController):
    # this url should actually work, but it refuses connection in tests without webtest
    _url = 'csv://127.0.0.1:8080/extractions/view/1.csv'

    csv_mocking_data = type('mocktype', (object,), {
        'headers': {'content-type': 'text/csv'},
        'content': '''user_name;age;token
admin;675;
editor;806;
guest;0;9ecf82c7e7ba11dbfea20cb84773339aff4d5f79''',
    })
    csv_mocking_data_wrong = type('mocktype', (object,), {
        'headers': {'content-type': 'text/plain'},
        'content': '''user_name;age;token
admin;675;
editor;806;
guest;0;9ecf82c7e7ba11dbfea20cb84773339aff4d5f79''',
    })

    @patch('requests.get', Mock(return_value=csv_mocking_data))
    def test_execute_query_users(self):
        result = self.get_session().execute(self._query_users)
        assert isinstance(result, DataFrame), type(result)
        assert len(result) == 3, result
        
    @patch('requests.get', Mock(return_value=csv_mocking_data_wrong))
    def test_execute_wrong_table(self):
        super(TestCsvDBSession, self).test_execute_wrong_table()

class TestJsonDBSession(AbstractDBSessions, TestController):
    # this url should actually work, but it refuses connection in tests without webtest
    _url = 'json://127.0.0.1:8080/extractions/view/1.json'

    class Mocktype(object):
        def __init__(self, content_type='application/json'):
            self.headers = {'content-type': content_type}
            
        def json(self):
            return [
                {"user_name": "admin", "age": 675, "token": ""},
                {"user_name": "editor", "age": 806, "token": ""},
                {"user_name": "guest", "age": 0, "token": "9ecf82c7e7ba11dbfea20cb84773339aff4d5f79"}
            ]


    json_mocking_data = Mocktype()
    json_mocking_data_wrong = Mocktype(content_type='text/plain')

    @patch('requests.get', Mock(return_value=json_mocking_data))
    def test_execute_query_users(self):
        result = self.get_session().execute(self._query_users)
        assert isinstance(result, DataFrame), type(result)
        assert len(result) == 3, result
        
    @patch('requests.get', Mock(return_value=json_mocking_data_wrong))
    def test_execute_wrong_table(self):
        super(TestJsonDBSession, self).test_execute_wrong_table()

class TestUnavailableDBSession(TestController):
    _url = 'unavailable://this_raises_keyerror'
    def test_unavailable(self):
        with assert_raises(KeyError) as ar:
            session_factory(self._url)
        assert str(ar.exception) == "'Unable to find a supported engine for {}'".format(self._url), str(ar.exception)
