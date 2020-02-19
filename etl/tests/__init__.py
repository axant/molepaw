# -*- coding: utf-8 -*-
"""Unit and functional test suite for etl."""

from os import getcwd
from paste.deploy import loadapp
from webtest import TestApp
from gearbox.commands.setup_app import SetupAppCommand
from tg import config, cache
from tg.util import Bunch
from etl.model.datasource import reset_cache
from random import randint

from etl import model
import transaction

__all__ = ['setup_app', 'setup_db', 'teardown_db', 'TestController']

application_name = 'main_without_authn'

def load_app(name=application_name):
    """Load the test application."""
    return TestApp(loadapp('config:test.ini#%s' % name, relative_to=getcwd()))


def setup_app():
    """Setup the application."""
    cmd = SetupAppCommand(Bunch(options=Bunch(verbose_level=1)), Bunch())
    cmd.run(Bunch(config_file='config:test.ini', section_name=None))


def setup_db():
    """Create the database schema (not needed when you run setup_app)."""
    engine = config['tg.app_globals'].sa_engine
    model.init_model(engine)
    model.metadata.create_all(engine)


def teardown_db():
    """Destroy the database schema."""
    engine = config['tg.app_globals'].sa_engine
    model.metadata.drop_all(engine)


class TestController(object):
    """Base functional test case for the controllers.

    The etl application instance (``self.app``) set up in this test
    case (and descendants) has authentication disabled, so that developers can
    test the protected areas independently of the :mod:`repoze.who` plugins
    used initially. This way, authentication can be tested once and separately.

    Check etl.tests.functional.test_authentication for the repoze.who
    integration tests.

    This is the officially supported way to test protected areas with
    repoze.who-testutil (http://code.gustavonarea.net/repoze.who-testutil/).

    """
    application_under_test = application_name

    manager_env = {'REMOTE_USER': 'manager'}
    admin_env = {'REMOTE_USER': 'admin'}

    def setUp(self):
        """Setup test fixture for each functional test method."""
        self.app = load_app(self.application_under_test)
        setup_app()

    def tearDown(self):
        """Tear down test fixture for each functional test method."""
        reset_cache()
        model.DBSession.remove()
        teardown_db()

    def flush(self):
        """flush db"""
        model.DBSession.flush()
        transaction.commit()

    def create_extraction(self, name=u'extraction one', category=None):
        extraction = model.Extraction(
            name=name, 
            category=category,
            uid=randint(1, 1000)
        )
        model.DBSession.add(extraction)
        return extraction

    def create_datasource(
        self,
        name=u'datasource one',
        url=u'sqlite:///etl/tests/testdatasource.db',
    ):
        ds = model.Datasource(
            name=name,
            url=url,
            uid=randint(1, 1000)
        )
        model.DBSession.add(ds)
        return ds

    def create_dataset(
        self,
        datasource,
        name=u'dataset one',
        query=u'SELECT * FROM tg_user'
    ):
        dataset = model.DataSet(
            name=name,
            query=query,
            datasource=datasource,
            uid=randint(1, 1000)
        )
        model.DBSession.add(dataset)
        return dataset
