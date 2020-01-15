import pandas as pd 
import collections 

from etl.lib.helpers import is_number, is_boolean, is_datetime
from etl import model
from etl.tests.models import ModelTest


class TestDataset(ModelTest):

	klass = model.DataSet
	attrs = dict(
		uid=1,
		name="Film",
		query="select * from film"
	)

	def test_csv(self):
		df = pd.read_csv('etl/tests/film.csv')
		for i in df.columns:
			# test_is_boolean
			if collections.Counter([is_boolean(j) for j in df[i].head(100).tolist()]).most_common(1)[0][0]:
				df[i] = df[i].astype('bool', errors='ignore')
				assert i == 'hire_price'
			# test_is_datetime
			elif collections.Counter([is_datetime(j) for j in df[i].head(100).tolist()]).most_common(1)[0][0]:
				df[i] = pd.to_datetime(df[i], errors='coerce')
				assert i in ('agreement_expiration', 'release_date', 'hire_price')
			# test_is_number
			elif collections.Counter([is_number(j) for j in df[i].head(100).tolist()]).most_common(1)[0][0]:
				df[i] = pd.to_numeric(df[i], errors='coerce')
				assert i in (
					'id', 'duration', 'phone_number', 'INDEX', 'campaing_end_date',
					'created_from_manager_id', 'campaing_start_date', 'birth_date'
				)

		assert df['hire_price'].dtypes.name == 'bool'
		assert df['agreement_expiration'].dtypes.name == df['release_date'].dtypes.name == 'datetime64[ns]'
		assert df['id'].dtypes.name == 'int64'
