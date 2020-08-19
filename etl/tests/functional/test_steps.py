import pandas as pd
import numpy as np
from etl.lib import steps
from datetime import datetime


class TestSteps(object):

    def test_slice(self):
        df = pd.DataFrame({
            'value': pd.Series([1, 2, 3]),
            'city': pd.Series(['TO', 'AL', 'MI']),
        })
        sliced = steps.slice_dataframe(df, ['city'])
        assert sliced['city'].any()
        try:
            sliced['value']
            assert False, 'should raise'
        except KeyError:
            pass

    def test_group(self):
        df = pd.DataFrame({
            'value': pd.Series([1, 1, 3]),
            'population': pd.Series([500, 100, 600]),
            'city': pd.Series(['TO', 'AL', 'MI']),
        })
        grouped = steps.group(df, 'sum', by='value')
        assert len(grouped) == 2
        assert grouped['value'][0] == 1
        assert grouped['population'][0] == 600
        assert grouped['population'][1] == 600
        try:
            grouped['city']
            assert False, 'actually why isn\'t it here?'
        except KeyError:
            pass

    def test_setvalue(self):
        df = pd.DataFrame({
            'value': pd.Series([1, 2, 3]),
            'population': pd.Series([500, 100, 600]),
            'city': pd.Series(['TO', 'AL', 'MI']),
        })
        df = steps.setvalue(df, 'new_population', 'population + 100')
        df = steps.setvalue(df, 'now', '@utcnow')
        df = steps.setvalue(df, 'nans', '@nan')
        df = steps.setvalue(df, 'value', '@null')
        assert df['new_population'][0] == 600
        assert df['now'][0] < datetime.utcnow()
        # assert df['nans'][0] == np.float64('nan'), df['nans'][0]
        assert str(df['nans'][0]) == 'nan', df['nans'][0]
        assert df['value'][0] == None
        assert df['city'][0] == 'TO'

    def test_striptime(self):
        df = pd.DataFrame({
            'value': pd.Series([1, 2, 3]),
            'population': pd.Series([500, 100, 600]),
            'city': pd.Series(['TO', 'AL', 'MI']),
        })
        df = steps.setvalue(df, 'now', '@utcnow')
        df = steps.striptime(df, 'now')
        assert df['now'][0] == datetime.utcnow().date()
        assert df['city'][0] == 'TO'
        df = steps.striptime(df, 'city')
        assert df['city'][0] is None

    def test_stripday(self):
        df = pd.DataFrame({
            'value': pd.Series([1, 2, 3]),
            'population': pd.Series([500, 100, 600]),
            'city': pd.Series(['TO', 'AL', 'MI']),
        })
        df = steps.setvalue(df, 'now', '@utcnow')
        df = steps.stripday(df, 'now')
        assert df['now'][0].year == datetime.utcnow().year
        assert df['now'][0].month == datetime.utcnow().month
        assert df['now'][0].day == 1
        assert df['city'][0] == 'TO'
        df = steps.stripday(df, 'city')
        assert df['city'][0] is None

    def test_timeago(self):
        df = pd.DataFrame({
            'value': pd.Series([1, 2, 3]),
            'population': pd.Series([500, 100, 600]),
            'city': pd.Series(['TO', 'AL', 'MI']),
        })
        df = steps.setvalue(df, 'now', '@utcnow')
        df = steps.timeago(df, 'now')
        assert df['now'][0] == 0
        df = steps.setvalue(df, 'now', '@utcnow')
        df['now'] = df['now'] - pd.DateOffset(weeks=1)
        df = steps.timeago(df, 'now')
        assert df['now'][0] == 7
        df = steps.setvalue(df, 'now', '@null')
        df = steps.timeago(df, 'now')
        assert df['now'][0] is None
        df = steps.timeago(df, 'value')
        assert df['value'][0] is None

    def test_rename(self):
        df = pd.DataFrame({
            'value': pd.Series([1, 2, 3]),
            'population': pd.Series([500, 100, 600]),
            'city': pd.Series(['TO', 'AL', 'MI']),
        })
        df = steps.rename(df, 'city', 'city_name')
        assert df['city_name'][0] == 'TO'
        try:
            df['city']
            assert False, 'should raise'
        except:
            pass

    def test_query(self):
        df = pd.DataFrame({
            'value': pd.Series([1, 2, 3]),
            'population': pd.Series([500, 100, 600]),
            'city': pd.Series(['TO', 'AL', 'MI']),
        })
        df = steps.query(df, 'city == "TO"')
        assert df['city'][0] == 'TO'
        assert len(df) == 1

    def test_setindex(self):
        df = pd.DataFrame({
            'value': pd.Series([1, 2, 3]),
            'population': pd.Series([500, 100, 600]),
            'city': pd.Series(['TO', 'AL', 'MI']),
        })
        isinstance(df.index, pd.core.indexes.range.RangeIndex)
        df.index[0] == 0
        df = steps.setindex(df, 'city')
        df.index[0] == 'TO'
        df = steps.setindex(df, 'population')
        df.index[0] == 500

    def test_concatcols(self):
        df = pd.DataFrame({
            'value': pd.Series([1, 2, 3]),
            'population': pd.Series([500, 100, 600]),
            'city': pd.Series(['TO', 'AL', 'MI']),
        })
        df = steps.concatcols(df, ['city', 'population'])
        assert df['city_population'][0] == 'TO_500'
        assert df['city'][0] == 'TO'
        assert df['population'][0] == 500

    def test_sort(self):
        df = pd.DataFrame({
            'value': pd.Series([1, 2, 3]),
            'population': pd.Series([500, 100, 600]),
            'city': pd.Series(['TO', 'AL', 'MI']),
        })
        df = steps.sort(df, ['population'])
        # remember to use the index for getting if tou rely on sort
        assert df['population'][df.index[0]] == 100
        assert df['city'][df.index[0]] == 'AL'
        assert df['population'][df.index[1]] == 500
        assert df['city'][df.index[1]] == 'TO'

    def test_sort_descending(self):
        df = pd.DataFrame({
            'value': pd.Series([1, 2, 3]),
            'population': pd.Series([500, 100, 600]),
            'city': pd.Series(['TO', 'AL', 'MI']),
        })
        df = steps.sort(df, ['-population'])
        # remember to use the index for getting if tou rely on sort
        assert df['population'][df.index[0]] == 600
        assert df['city'][df.index[0]] == 'MI'
        assert df['population'][df.index[1]] == 500
        assert df['city'][df.index[1]] == 'TO'


    def test_linkize(self):
        df = pd.DataFrame({
            'value': pd.Series([1, 2, 3]),
            'population': pd.Series([500, 100, 600]),
            'city': pd.Series(['TO', 'AL', 'MI']),
        })
        df = steps.linkize(df, 'city', 'http://italy.it/{}')
        assert '<a class="" href="http://italy.it/TO">http://italy.it/TO</a>' == df['city'][0], df['city'][0]
        df = pd.DataFrame({
            'value': pd.Series([1, 2, 3]),
            'population': pd.Series([500, 100, 600]),
            'city': pd.Series(['TO', 'AL', 'MI']),
        })
        df = steps.linkize(df, 'city', 'http://italy.it/{}', name='view')
        assert '<a class="btn btn-info" href="http://italy.it/TO">view</a>' == df['city'][0], df['city'][0]
        df = steps.linkize(df, 'city', 33)
        assert df['city'][0] is None, df['city'][0]

    def test_duplicated(self):
        df = pd.DataFrame({
            'value': pd.Series([1.3, 2.999999999, 3.1415, 0, 0, 0, 0]),
            'city': pd.Series(['TO', 'AL', 'MI', 'AL', 'NA', 'AL', 'AL']),
        })
        df = steps.duplicated(df, None, None)
        assert df['duplicated_all_fields'].tolist() == [False, False, False, False, False, True, True]
        del df['duplicated_all_fields']
        df = steps.duplicated(df, None, 'last')
        assert df['duplicated_all_fields'].tolist() == [False, False, False, True, False, True, False]
        del df['duplicated_all_fields']
        df = steps.duplicated(df, None, 'False')
        assert df['duplicated_all_fields'].tolist() == [False, False, False, True, False, True, True]
        del df['duplicated_all_fields']
        df = steps.duplicated(df, ['city'], 'False')
        assert df['duplicated_city'].tolist() == [False, True, False, True, False, True, True]
        del df['duplicated_city']

    def test_cast_to_int(self):
        df = pd.DataFrame({
            'value': pd.Series([1.3, 2.999999999, 3.1415]),
            'city': pd.Series(['TO', 'AL', 'MI']),
        })
        df = steps.cast_to_int(df, ['value'])
        assert df['value'][0] == '1'
        assert df['value'][1] == '3'
        assert df['value'][2] == '3'
        assert df['value'].dtype.name == 'object'
