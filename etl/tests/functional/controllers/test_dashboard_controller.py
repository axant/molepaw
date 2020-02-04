from etl.tests.functional.controllers import BaseTestController
from etl.model import DBSession
from etl import model
import transaction


class TestDashboardController(BaseTestController):

    def create_extraction_association(self, dashboard_uid, index):
        dashboard_extraction_association = model.DashboardExtractionAssociation(
            dashboard_id=dashboard_uid,
            extraction_id=self.extraction,
            index=index,
            visualization='histogram',
            graph_axis='email_address,user_id'
        )
        DBSession.add(dashboard_extraction_association)
        DBSession.flush()
        return dashboard_extraction_association

    def create_dashboard(self, name='Test purpose dashboard', index=0):
        entities = dict()
        dashboard = model.Dashboard(
           name=name
        )
        transaction.begin()
        DBSession.add(dashboard)
        DBSession.flush()
        entities.update(dict(dashboard=dashboard.uid))
        dashboard_extraction_association = self.create_extraction_association(
            dashboard.uid, index
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
                'index': 1
            },
            extra_environ=self.admin_env,
            status=200
        )

        assert response.json == {
            'de': {
                'dashboard_id': 1,
                'extraction_id': 1,
                'visualization': 'histogram',
                'graph_axis': 'email_address,user_id',
                'index': 1
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
                'extraction_id': 1,
                'uid': 1,
                'graph_axis': 'display_name,user_id',
                'dashboard': {
                    'name': 'Test purpose dashboard',
                    'uid': 1
                },
                'extraction': {
                    'uid': 1,
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
                'uid': 1,
                'visualization': 'table',
                'graph_axis': None,
                'name': 'default_ext',
                'category_id': 1
            }
        }

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

        # Case 3 - the last become the first and vice versa
        response = self.app.put_json(
            '/dashboard/set_extraction_index/' + str(entities['dashboard']),
            {'uid': entities['dashboard_extraction_association_2'], 'index': 0},
            extra_environ=self.admin_env,
            status=200
        )

        assert response.json['de']['index'] == 0
        assert response.json['other_de']['index'] == 1

