# -*- coding: utf-8 -*-
from etl.tests import TestController
from etl import model


class TestDatasets(TestController):
    def test_index(self):
        extraction = self.create_extraction()
        datasource = self.create_datasource()
        dataset1 = self.create_dataset(datasource=datasource)
        self.flush()
        r = self.app.get('/datasets', status=200, extra_environ=self.manager_env)
        assert 'dataset one' in r.text, r.text

    def test_view(self):
        extraction = self.create_extraction()
        datasource = self.create_datasource()
        dataset1 = self.create_dataset(datasource=datasource)
        self.flush()
        dataset1 = model.DBSession.merge(dataset1)
        r = self.app.get(
            '/datasets/view/%s' % dataset1.uid,
            status=200,
            extra_environ=self.manager_env,
        )

        assert '<h3><span id="results-count">3</span> Results</h3>' in r.text, r.text
        # assert all fields are present for each result
        assert 'admin' in r.text, r.text
        assert 'admin@somedomain.com' in r.text, r.text
        assert 'Example Admin' in r.text, r.text
        assert 'fba0f3a1d7c6ca3afd2d60d68ca61412f20e770bce6ee7b596d3b374d93716daef9e5e6f922d0b0aed1a4ded00c485a181bd6c46cfa1e7f40ae6559483b1f2a8' in r.text, r.text
        assert '2018-09-11 17:04:42.240496' in r.text, r.text

    def test_broken_fetch(self):
        extraction = self.create_extraction()
        datasource = self.create_datasource(url=u'nonenonenone')
        dataset = self.create_dataset(datasource=datasource)
        self.flush()
        dataset = model.DBSession.merge(dataset)
        r = self.app.get(
            '/datasets/view/%s' % dataset.uid,
            status=200,
            extra_environ=self.admin_env,
        )

        assert 'ERROR: ' in r.text, r.text

    def test_dataset_csv(self):
        extraction = self.create_extraction()
        datasource = self.create_datasource()
        dataset = self.create_dataset(datasource=datasource)
        self.flush()
        dataset = model.DBSession.merge(dataset)
        r = self.app.get(
            '/datasets/view.csv?dataset=%s' % dataset.uid,
            status=200,
            extra_environ=self.manager_env,
        )
        assert r.text.startswith(
            u'"INDEX","user_id","user_name","email_address","display_name","password","created"\r\n0,1,"admin","admin@somedomain.com","Example Admin","fba0f3a1d7c6ca3afd2d60d68ca61412f20e770bce6ee7b596d3b374d93716daef9e5e6f922d0b0aed1a4ded00c485a181bd6c46cfa1e7f40ae6559483b1f2a8","2018-09-11 17:04:42.240496"\r\n'
        ), r.text

    def test_dataset_json(self):
        extraction = self.create_extraction()
        datasource = self.create_datasource()
        dataset = self.create_dataset(datasource=datasource)
        self.flush()
        dataset = model.DBSession.merge(dataset)
        r = self.app.get(
            '/datasets/view.json?dataset=%s' % dataset.uid,
            status=200,
            extra_environ=self.manager_env,
        )
        assert len(r.json) == 3, r.json
        assert r.json[0]['user_id'] == 1
        assert r.json[0]['user_name'] == 'admin'
        assert r.json[0]['email_address'] == 'admin@somedomain.com'
        assert r.json[0]['display_name'] == 'Example Admin'
        assert r.json[0]['password'] == 'fba0f3a1d7c6ca3afd2d60d68ca61412f20e770bce6ee7b596d3b374d93716daef9e5e6f922d0b0aed1a4ded00c485a181bd6c46cfa1e7f40ae6559483b1f2a8'
        assert r.json[0]['created'] in ['2018-09-11T17:04:42.240Z',
                                        '2018-09-11 17:04:42.240496'], r.json[0]['created']
