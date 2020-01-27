from etl.tests import TestController


class TestRootController(TestController):
    application_under_test = 'main'

    def test_authentication_failures(self):
        response = self.app.get(
            '/post_login'
        )
        redirection = response.follow()
        assert 'Wrong credentials' in redirection.body.decode('utf-8')

        response = self.app.get(
            '/login'
        )
        form = response.form
        form['login'] = 'non_exixsting_user'
        form['password'] = 'password'

        result = form.submit(status=302).follow()
        assert 'User not found' in result.body.decode('utf-8')


