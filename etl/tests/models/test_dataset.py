import pandas as pd
import collections
from etl import model
from etl.tests.models import ModelTest
from nose.tools import assert_raises
from mock import Mock, patch
from beaker.cache import Cache
import tg


class TestDataset(ModelTest):
    klass = model.DataSet
    attrs = dict(
        uid=1,
        name="Users",
        query="select * from tg_user"
    )

    def test_csv(self):
        df = pd.read_csv('etl/tests/film.csv')
        assert df['hire_price'].dtypes.name == 'bool'
        assert df['agreement_expiration'].dtypes.name == df['release_date'].dtypes.name == 'object',\
            (df['agreement_expiration'].dtypes.name, df['release_date'].dtypes.name)
        assert df['id'].dtypes.name == 'int64'
        df = self.klass.get_column_typed(df)
        assert df['hire_price'].dtypes.name in 'bool', df['hire_price'].dtypes.name
        assert df['agreement_expiration'].dtypes.name == df['release_date'].dtypes.name == 'datetime64[ns]',\
            (df['agreement_expiration'].dtypes.name, df['release_date'].dtypes.name)
        assert df['id'].dtypes.name == 'int64'

    def test_fetch_valueerror(self):
        assert_raises(ValueError, self.obj.fetch)

    error_mocked_cache = Mock(return_value=type('MockedCache', (object,), {'get_value': Mock(side_effect=KeyError)}))
    error_mock_cache = type('MockCache', (object,), {'get_cache': error_mocked_cache})
    mocked_cache = Mock(return_value=type('MockedCache', (object,), {'get_value': Mock(return_value='data')}))
    mock_cache = type('MockCache', (object,), {'get_cache': mocked_cache})

    @patch.object(tg, 'cache', mock_cache)
    def test_fetch(self):
        self.obj.datasource = model.Datasource(url='sqlite:///etl/tests/testdatasource.db')
        self.obj.fetch()

    @patch.object(tg, 'cache', error_mock_cache)
    @patch.object(collections, 'Counter', Mock(side_effect=Exception))
    def test_fetch_exception(self):
        self.obj.datasource = model.Datasource(url='sqlite:///etl/tests/testdatasource.db')
        assert_raises(Exception, self.obj.fetch)

    # this test is needed because tg_user doesn't have integers (we could add a field)
    csv_mocking_data = type('mocktype', (object,), {
        'headers': {'content-type': 'text/csv'},
        'content': '''"user_name","age","token","active"
"admin",675,,1
"editor",806,,0
"guest",0,"9ecf82c7e7ba11dbfea20cb84773339aff4d5f79",1''',
    })
    df = pd.DataFrame([
            ["admin", 675, "abcd", True],
            ["editor", 806, "abcd", False],
            ["guest", 0, "9ecf82c7e7ba11dbfea20cb84773339aff4d5f79", True]
        ],
        columns=["user_name", "age", "token", "active"]
    )
    csv_mocked_cache = Mock(return_value=type('MockedCache', (object,), {'get_value': Mock(return_value=df)}))
    csv_mock_cache = type('MockCache', (object,), {'get_cache': csv_mocked_cache})

    @patch.object(tg, 'cache', csv_mock_cache)
    @patch('requests.get', Mock(return_value=csv_mocking_data))
    def test_fetch_csv(self):
        self.obj.datasource = model.Datasource(url='csv://127.0.0.1:8080/extractions/view/1.csv')
        from etl.model.datasource import DS_CACHE
        from etl.lib.dbsessions.http_csv import HTTPCSVSession
        DS_CACHE.set_value(
            self.obj.datasource.cache_key,
            HTTPCSVSession(url=self.obj.datasource.url)
        )
        df = self.obj.fetch()
        assert isinstance(self.obj.datasource.dbsession, HTTPCSVSession)
        assert df['age'].dtype.name == 'int64'
        assert df['age'][0] == 675
        assert df['user_name'].dtype.name == 'object'
        assert df['user_name'][0] == 'admin'
        assert df['token'].dtype.name == 'object'
        assert df['token'][0] == 'abcd'
        assert df['active'].dtype.name == 'bool'
        assert df['active'][0]

    @patch.object(tg, 'cache', type('MockCache', (object,), {'get_cache': Cache}))
    @patch.object(model.datasource, 'DS_CACHE', Cache('mocked'))
    def test_fetch_sqlite3_dtypes(self):
        self.obj.datasource = model.Datasource(url='sqlite:///etl/tests/testdatasource.db')
        self.obj.query = 'select * from types_of_data'
        df = self.obj.fetch()
        assert df['int_only'].dtype.name == 'int64'
        assert df['float_only'].dtype.name == 'float64'
        assert df['string_only'].dtype.name == 'object'
        assert df['isoformat'].dtype.name == 'datetime64[ns]'
        assert df['only_1'].dtype.name != 'bool'
        assert df['only_1'].dtype.name == 'int64'
        assert df['only_0'].dtype.name != 'bool'
        assert df['only_0'].dtype.name == 'int64'
        assert df['only_0_and_1'].dtype.name != 'bool'
        assert df['only_0_and_1'].dtype.name == 'int64'
        assert df['int_as_string'].dtype.name == 'int64'
        assert df['float_as_string'].dtype.name == 'float64'
        assert df['nulls_text'].dtype.name == 'object'
        assert df['only_1_text'].dtype.name == 'bool'
        assert df['only_0_text'].dtype.name == 'bool'
        assert df['only_0_and_1_text'].dtype.name == 'bool'
        assert df['int_with_null'].dtype.name == 'int64'
