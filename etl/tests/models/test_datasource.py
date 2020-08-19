from etl import model
from etl.tests.models import ModelTest
from mock import Mock, patch
from beaker.cache import Cache
import tg


class TestDatasource(ModelTest):
    klass = model.Datasource
    attrs = dict(
        uid=1,
        name="sqlite_testdata",
        url="sqlite:///etl/tests/testdatasource.db"
    )

    def test_fetch(self):
        # this is similar to etl.tests.models.test_datasets:TestDataset.test_fetch_sqlite3_dtypes
        # but as you can see data is still not converted here
        df = self.obj.dbsession.execute('select * from types_of_data')
        assert df['int_only'].dtype.name == 'int64'
        assert df['float_only'].dtype.name == 'float64'
        assert df['string_only'].dtype.name == 'object'
        assert df['isoformat'].dtype.name != 'datetime64[ns]'
        assert df['isoformat'].dtype.name == 'object'
        assert df['only_1'].dtype.name != 'bool'
        assert df['only_1'].dtype.name == 'int64'
        assert df['only_0'].dtype.name != 'bool'
        assert df['only_0'].dtype.name == 'int64'
        assert df['only_0_and_1'].dtype.name != 'bool'
        assert df['only_0_and_1'].dtype.name == 'int64'
        assert df['int_as_string'].dtype.name == 'object'
        assert df['float_as_string'].dtype.name == 'object'
        assert df['nulls_text'].dtype.name == 'object'
        assert df['only_1_text'].dtype.name == 'object'
        assert df['only_0_text'].dtype.name == 'object'
        assert df['only_0_and_1_text'].dtype.name == 'object'
        assert df['int_with_null'].dtype.name != 'int64'
        assert df['int_with_null'].dtype.name == 'float64'
