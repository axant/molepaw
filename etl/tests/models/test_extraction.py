from etl import model
from etl.tests import create_datasource, create_dataset, create_extraction_dataset
from etl.tests.models import ModelTest
from mock import patch
from beaker.cache import Cache
import tg


class TestExtraction(ModelTest):
    klass = model.Extraction
    attrs = dict(
        uid=1,
        name="test extraction 1",
    )

    def after_creation(self):
        datasource = create_datasource()
        users = create_extraction_dataset(self.obj, create_dataset(datasource))
        users_to_groups = create_extraction_dataset(
            self.obj,
            create_dataset(
                datasource,
                name='users_to_group',
                query='select * from tg_user_group',
            ),
            priority=1,
            join_self_col='user_id',
            join_other_col='user_id',
        )
        groups = create_extraction_dataset(
            self.obj,
            create_dataset(
                datasource,
                name='groups',
                query='select * from tg_group',
            ),
            priority=2,
            join_self_col='group_id',
            join_other_col='group_id',
        )
        return {'datasets': [users, users_to_groups, groups]}

    @patch.object(tg, 'cache', type('MockCache', (object,), {'get_cache': Cache}))
    def test_fetch(self):
        df = self.obj.fetch()
        assert df['user_id'].dtype.name == 'int64'
        assert df['user_name'].dtype.name == 'object'
        assert df['email_address'].dtype.name == 'object'
        assert df['display_name'].dtype.name == 'object'
        assert df['password'].dtype.name == 'object'
        assert df['created'].dtype.name == 'datetime64[ns]'
        assert df['group_id'].dtype.name == 'int64'
        assert df['group_name'].dtype.name == 'object'
        assert df['display_name_j_groups'].dtype.name == 'object'
        assert df['created_j_groups'].dtype.name == 'datetime64[ns]'
