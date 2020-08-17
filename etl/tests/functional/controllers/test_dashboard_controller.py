from etl.tests.functional.controllers import BaseTestController
from etl.model import DBSession
from etl import model
import transaction
from mock import patch, Mock


class TestDashboardController(BaseTestController):

    def create_extraction_association(
            self, dashboard_uid, index,
            visualization='histogram',
            graph_axis='email_address,user_id',
            columns=4,
    ):
        dashboard_extraction_association = model.DashboardExtractionAssociation(
            dashboard_id=dashboard_uid,
            extraction_id=self.extraction,
            index=index,
            visualization=visualization,
            graph_axis=graph_axis,
            columns=columns,
        )
        DBSession.add(dashboard_extraction_association)
        DBSession.flush()
        return dashboard_extraction_association

    def create_dashboard(
            self, name='Test purpose dashboard', index=0,
            visualization='histogram',
            graph_axis='email_address,user_id'
    ):
        entities = dict()
        dashboard = model.Dashboard(
           name=name
        )
        transaction.begin()
        DBSession.add(dashboard)
        DBSession.flush()
        entities.update(dict(dashboard=dashboard.uid))
        dashboard_extraction_association = self.create_extraction_association(
            dashboard.uid, index,
            visualization=visualization,
            graph_axis=graph_axis,
            columns=4,
        )
        entities.update(dict(
            dashboard_extraction_association=dashboard_extraction_association.uid
        ))
        transaction.commit()
        return entities

    def test_index(self):
        entities = self.create_dashboard()
        response = self.app.get(
            '/dashboard',
            extra_environ=self.admin_env,
            status=200
        )

        assert 'Dahboard: Test purpose dashboard' in response.text
        assert 'Edit Dashboard' in response.text

        response = self.app.get(
            '/dashboard',
            params=dict(id=entities['dashboard']),
            extra_environ=self.admin_env,
            status=200
        )

        assert 'Dahboard: Test purpose dashboard' in response.text
        assert 'Edit Dashboard' in response.text

    def test_index_no_dashboard(self):
        response = self.app.get(
            '/dashboard',
            extra_environ=self.admin_env,
            status=404
        )
        assert 'dashboard not found' in response.text

    def test_new_and_save_name(self):
        response = self.app.get(
            '/dashboard/new',
            extra_environ=self.admin_env,
            status=200
        )

        assert response.html.find(
            id="dashboard_name"
        ).get_text() == 'New dashboard'
        form = response.form
        form['name'] = 'New dashboard for test purpose'

        # unauthorized case
        form.submit(status=401)

        # wrong uid case
        form['uid'] = 69
        form.submit(
            extra_environ=self.admin_env,
            status=404
        )
        # working case
        form['uid'] = 1
        submission = form.submit(
            extra_environ=self.admin_env,
            status=302
        ).follow(extra_environ=self.admin_env)
        assert submission.html.find(
            id="dashboard_name"
        ).get_text() == 'New dashboard for test purpose'

    def test_delete(self):
        default_entities = self.create_dashboard()
        custom_entities = self.create_dashboard(name='Custom dashboard')

        # CASE 1:
        # admin trying to delete the default dashboard => Error 400 Bad request
        self.app.get(
            '/dashboard/delete',
            params=dict(dashboard_id=default_entities['dashboard']),
            extra_environ=self.admin_env,
            status=400
        )

        # CASE 2
        # Normal user try to delete a dashboard => Error 403 Forbidden
        self.app.get(
            '/dashboard/delete',
            params=dict(dashboard_id=custom_entities['dashboard']),
            extra_environ=self.manager_env,
            status=403
        )

        # Case 3
        # Admin try to delete custonm dashboard (not default) => Success 302
        response = self.app.get(
            '/dashboard/delete',
            params=dict(dashboard_id=custom_entities['dashboard']),
            extra_environ=self.admin_env,
            status=302
        ).follow(extra_environ=self.admin_env)

        assert 'Dahboard: Test purpose dashboard' in response.text
        assert 'Edit Dashboard' in response.text
        assert DBSession.query(model.Dashboard).get(
            custom_entities['dashboard']
        ) is None

    def test_edit(self):
        entities = self.create_dashboard()

        # Case 1 - admin wrong dashboard uid => Error 404
        self.app.get(
            '/dashboard/edit',
            params=dict(id=69),
            extra_environ=self.admin_env,
            status=404
        )

        # Case 2 - non admin => Forbidden 403
        self.app.get(
            '/dashboard/edit',
            params=dict(id=entities['dashboard']),
            extra_environ=self.manager_env,
            status=403
        )

        # Case 3 - Admin and right dashboard => Ok 200
        response = self.app.get(
            '/dashboard/edit',
            params=dict(id=entities['dashboard']),
            extra_environ=self.admin_env,
            status=200
        )
        form = response.form
        form['name'] = 'New dashboard for test purpose'

        submission = form.submit(
            extra_environ=self.admin_env,
            status=302
        ).follow(extra_environ=self.admin_env)
        assert submission.html.find(
            id="dashboard_name"
        ).get_text() == 'New dashboard for test purpose'

    def test_save_extraction(self):
        entities = self.create_dashboard()
        response = self.app.post_json(
            '/dashboard/save_extraction/' + str(entities['dashboard']),
            {
                'graph_axis': 'email_address,user_id',
                'visualization': 'histogram',
                'extraction_id': self.extraction,
                'index': 1,
                'columns': 8,
            },
            extra_environ=self.admin_env,
            status=200
        )

        assert response.json == {
            'de': {
                'dashboard_id': 1,
                'extraction_id': self.extraction,
                'visualization': 'histogram',
                'graph_axis': 'email_address,user_id',
                'index': 1,
                'columns': 8,
            },
            'dashboard': None,
            'extraction': None
        }

        response = self.app.post_json(
            '/dashboard/save_extraction/' + str(entities['dashboard']),
            {
                'graph_axis': 'display_name,user_id',
                'visualization': 'histogram',
                'extraction_id': self.extraction,
                'index': 0,
                'columns': 4,
                'uid': entities['dashboard_extraction_association']
            },
            extra_environ=self.admin_env,
            status=200
        )

        assert response.json == {
            'de': {
                'dashboard_id': 1,
                'index': 0,
                'visualization': 'histogram',
                'extraction_id': self.extraction,
                'uid': 1,
                'graph_axis': 'display_name,user_id',
                'columns': 4,
                'dashboard': {
                    'name': 'Test purpose dashboard',
                    'uid': 1
                },
                'extraction': {
                    'uid': self.extraction,
                    'visualization': 'table',
                    'graph_axis': None,
                    'name': 'default_ext',
                    'category_id': 1
                }
            },
            'dashboard': {
                'name': 'Test purpose dashboard',
                'uid': 1
            },
            'extraction': {
                'uid': self.extraction,
                'visualization': 'table',
                'graph_axis': None,
                'name': 'default_ext',
                'category_id': 1
            }
        }

    def test_save_extraction_validate_columns(self):
        entities = self.create_dashboard()
        response = self.app.post_json(
            '/dashboard/save_extraction/' + str(entities['dashboard']),
            {
                'graph_axis': 'email_address,user_id',
                'visualization': 'histogram',
                'extraction_id': self.extraction,
                'index': 1,
                'columns': '8a',
            },
            extra_environ=self.admin_env,
            status=412,
        )
        assert 'integer' in response.json['detail']
        response = self.app.post_json(
            '/dashboard/save_extraction/' + str(entities['dashboard']),
            {
                'graph_axis': 'email_address,user_id',
                'visualization': 'histogram',
                'extraction_id': self.extraction,
                'index': 1,
                'columns': '80',
            },
            extra_environ=self.admin_env,
            status=412,
        )
        assert 'integer' not in response.json['detail']

    def test_delete_extraction(self):
        entities = self.create_dashboard()
        # wrong uid no deletion
        response = self.app.delete_json(
            '/dashboard/delete_extraction/' + str(entities['dashboard']),
            dict(uid=69),
            extra_environ=self.admin_env,
            status=200
        )
        assert response.json == dict()
        assert DBSession.query(
            model.DashboardExtractionAssociation
        ).get(entities['dashboard_extraction_association']) is not None
        # wright uid effective deletion
        response = self.app.delete_json(
            '/dashboard/delete_extraction/' + str(entities['dashboard']),
            dict(uid=entities['dashboard_extraction_association']),
            extra_environ=self.admin_env,
            status=200
        )
        assert response.json == dict()
        assert DBSession.query(
            model.DashboardExtractionAssociation
        ).get(entities['dashboard_extraction_association']) is None

    def test_set_extraction_index(self):
        entities = self.create_dashboard()
        transaction.begin()
        entities['dashboard_extraction_association_2'] = self.create_extraction_association(
            entities['dashboard'], 1
        ).uid
        transaction.commit()
        # Case 1 - wrong index < 0
        self.app.put_json(
            '/dashboard/set_extraction_index/' + str(entities['dashboard']),
            {'uid': entities['dashboard_extraction_association'], 'index': -10},
            extra_environ=self.admin_env,
            status=400
        )

        # Case 2 - wrong index > last_index
        self.app.put_json(
            '/dashboard/set_extraction_index/' + str(entities['dashboard']),
            {'uid': entities['dashboard_extraction_association'], 'index': 10},
            extra_environ=self.admin_env,
            status=400
        )

        # Case 3 - wrong association_id - NoResultFound
        self.app.put_json(
            '/dashboard/set_extraction_index/' + str(entities['dashboard']),
            {'uid': 123, 'index': 1},
            extra_environ=self.admin_env,
            status=404
        )

        # Case 4 - the last become the first and vice versa
        response = self.app.put_json(
            '/dashboard/set_extraction_index/' + str(entities['dashboard']),
            {'uid': entities['dashboard_extraction_association_2'], 'index': 0},
            extra_environ=self.admin_env,
            status=200
        )

        assert response.json['de']['index'] == 0
        assert response.json['other_de']['index'] == 1
        assert DBSession.query(
            model.DashboardExtractionAssociation
        ).get(entities['dashboard_extraction_association']).index == 1
        assert DBSession.query(
            model.DashboardExtractionAssociation
        ).get(entities['dashboard_extraction_association_2']).index == 0

    def test_extractions(self):
        entities = self.create_dashboard()
        # Case 1 - not admin
        self.app.get(
            '/dashboard/extractions/' + str(entities['dashboard']),
            extra_environ=self.manager_env,
            status=403
        )

        # Case 2 - admin
        response = self.app.get(
            '/dashboard/extractions/' + str(entities['dashboard']),
            extra_environ=self.admin_env,
            status=200
        )

        assert len(response.json['extractions']) == 1
        assert response.json['extractions'][0]['uid'] == self.extraction
        assert response.json['dashboard']['uid'] == entities['dashboard']

        # Case 3 - wrong dashboard uid
        self.app.get(
            '/dashboard/extractions/' + str(69),
            extra_environ=self.admin_env,
            status=404
        )

    def test_get_extraction(self):
        # Case 1 - no admin
        self.app.get(
            '/dashboard/get_extraction/' + str(self.extraction),
            extra_environ=self.manager_env,
            status=403
        )

        # Case 2 - Admin
        response = self.app.get(
            '/dashboard/get_extraction/' + str(self.extraction),
            extra_environ=self.admin_env,
            status=200
        )

        extraction = DBSession.query(model.Extraction).get(self.extraction)
        for key in response.json['extraction'].keys():
            assert response.json['extraction'][key] == getattr(extraction, key, None)

        # Case 3 - wrong extraction uid
        self.app.get(
            '/dashboard/get_extraction/' + str(69),
            extra_environ=self.admin_env,
            status=404
        )

    def test_extraction_widget_histogram(self):
        entities = self.create_dashboard()
        response = self.app.get(
            '/dashboard/extraction_widget/' + str(entities['dashboard']),
            params=dict(uid=entities['dashboard_extraction_association']),
            extra_environ=self.admin_env,
            status=200
        )

        assert 'default_ext' in response.text
        assert len(
            response.html.find_all('div', class_="bk-root")
        ) > 0

    @patch(
        'etl.controllers.dashboard.figure',
        Mock(side_effect=Exception('Fake Error'))
    )
    def test_extraction_widget_histogram_error(self):
        entities = self.create_dashboard()
        response = self.app.get(
            '/dashboard/extraction_widget/' + str(entities['dashboard']),
            params=dict(uid=entities['dashboard_extraction_association']),
            extra_environ=self.admin_env,
            status=302
        )
        response.follow(
            extra_environ=self.admin_env,
            status=404
        )

    def test_extraction_widget_pie(self):
        entities = self.create_dashboard(
            visualization='pie', graph_axis='email_address,user_id'
        )
        response = self.app.get(
            '/dashboard/extraction_widget/' + str(entities['dashboard']),
            params=dict(uid=entities['dashboard_extraction_association']),
            extra_environ=self.admin_env,
            status=200
        )
        assert 'default_ext' in response.text
        assert len(
            response.html.find_all('div', class_="bk-root")
        ) > 0

    def test_extraction_widget_pie_multicolor(self):
        entities = self.create_dashboard(
            visualization='pie', graph_axis='email_address,user_id'
        )
        DBSession.query(model.ExtractionStep).delete()
        DBSession.flush()
        transaction.commit()
        response = self.app.get(
            '/dashboard/extraction_widget/' + str(entities['dashboard']),
            params=dict(uid=entities['dashboard_extraction_association']),
            extra_environ=self.admin_env,
            status=200
        )
        assert 'default_ext' in response.text
        assert len(
            response.html.find_all('div', class_="bk-root")
        ) > 0

    def test_extraction_widget_line(self):
        entities = self.create_dashboard(
            visualization='line', graph_axis='email_address,user_id'
        )
        response = self.app.get(
            '/dashboard/extraction_widget/' + str(entities['dashboard']),
            params=dict(uid=entities['dashboard_extraction_association']),
            extra_environ=self.admin_env,
            status=200
        )
        assert len(
            response.html.find_all('div', class_="bk-root")
        ) > 0
        assert 'default_ext' in response.text

    def test_extraction_widget_line_with_date(self):
        entities = self.create_dashboard(
            visualization='line', graph_axis='created,user_id'
        )
        response = self.app.get(
            '/dashboard/extraction_widget/' + str(entities['dashboard']),
            params=dict(uid=entities['dashboard_extraction_association']),
            extra_environ=self.admin_env,
            status=200
        )

        assert 'default_ext' in response.text
        assert len(
            response.html.find_all('div', class_="bk-root")
        ) > 0

    def test_extraction_widget_sum(self):
        entities = self.create_dashboard(
            visualization='sum', graph_axis='user_id'
        )
        response = self.app.get(
            '/dashboard/extraction_widget/' + str(entities['dashboard']),
            params=dict(uid=entities['dashboard_extraction_association']),
            extra_environ=self.admin_env,
            status=200
        )
        assert 'default_ext' in response.text
        assert len(
            response.html.find_all('div', class_="visualization-number")
        ) > 0
        assert '3', 'sum of user_id' in response.html.find_all('div', class_="visualization-number")[0].get_text()

    def test_extraction_widget_sum_wrong_type(self):
        entities = self.create_dashboard(
            visualization='sum', graph_axis='email_address'
        )
        response = self.app.get(
            '/dashboard/extraction_widget/' + str(entities['dashboard']),
            params=dict(uid=entities['dashboard_extraction_association']),
            extra_environ=self.admin_env,
            status=200
        )

        assert 'default_ext' in response.text
        assert len(
            response.html.find_all('div', class_="visualization-number")
        ) > 0
        assert 'admin@somedomain.commanager@somedomain.com'\
               in response.html.find_all('div', class_="visualization-number")[0].get_text()

    def test_extraction_widget_average(self):
        entities = self.create_dashboard(
            visualization='average', graph_axis='user_id'
        )
        response = self.app.get(
            '/dashboard/extraction_widget/' + str(entities['dashboard']),
            params=dict(uid=entities['dashboard_extraction_association']),
            extra_environ=self.admin_env,
            status=200
        )

        assert 'default_ext' in response.text
        assert len(
            response.html.find_all('div', class_="visualization-number")
        ) > 0
        assert '1.50' in response.html.find_all('div', class_="visualization-number")[0].get_text()
        assert 'average of user_id' in response.html.find_all('div', class_="visualization-number")[0].get_text()

    def test_extraction_widget_average_errors(self):
        entities = self.create_dashboard(
            visualization='average', graph_axis='display_name'
        )
        response = self.app.get(
            '/dashboard/extraction_widget/' + str(entities['dashboard']),
            params=dict(uid=entities['dashboard_extraction_association']),
            extra_environ=self.admin_env,
            status=200
        )

        assert 'Error' in response.html.find_all('div', class_="visualization-number")[0].get_text()
        assert 'average of display_name' in response.html.find_all(
            'div', class_="visualization-number"
        )[0].get_text()

    def test_wrong_visualization_error(self):
        entities = self.create_dashboard(
            visualization='wrongone', graph_axis='display_name'
        )
        response = self.app.get(
            '/dashboard/extraction_widget/' + str(entities['dashboard']),
            params=dict(uid=entities['dashboard_extraction_association']),
            extra_environ=self.admin_env,
            status=302
        )
        response = response.follow(
            extra_environ=self.admin_env,
            status=404
        )

    @patch(
        'etl.model.extraction.Extraction.perform',
        Mock(side_effect=Exception('Fake error'))
    )
    def test_extraction_widget_first_error(self):
        entities = self.create_dashboard()
        response = self.app.get(
            '/dashboard/extraction_widget/' + str(entities['dashboard']),
            params=dict(uid=entities['dashboard_extraction_association']),
            extra_environ=self.admin_env,
            status=302
        )
        redirection = response.follow(
            extra_environ=self.admin_env,
            status=404
        )
        assert 'ERROR RETRIEVING DATA:' in redirection.text
        assert 'Fake error' in redirection.text




