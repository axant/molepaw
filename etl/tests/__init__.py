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

def load_app(name=application_name, config='test.ini'):
    """Load the test application."""
    return TestApp(loadapp('config:%s#%s' % (config, name), relative_to=getcwd()))


def setup_app(config='test.ini'):
    """Setup the application."""
    cmd = SetupAppCommand(Bunch(options=Bunch(verbose_level=1)), Bunch())
    cmd.run(Bunch(config_file='config:%s' % config, section_name=None))


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

    def create_extraction(self, *a, **kw):
        return create_extraction(*a, **kw)

    def create_datasource(self, *a, **kw):
        return create_datasource(*a, **kw)

    def create_dataset(self, *a, **kw):
        return create_dataset(*a, **kw)


def create_extraction(name=u'extraction one', category=None):
    extraction = model.Extraction(
        name=name, 
        category=category,
        uid=randint(1, 100000)
    )
    model.DBSession.add(extraction)
    return extraction


def create_datasource(
    name=u'datasource one',
    url=u'sqlite:///etl/tests/testdatasource.db',
):
    ds = model.Datasource(
        name=name,
        url=url,
        uid=randint(1, 100000)
    )
    model.DBSession.add(ds)
    return ds


def create_dataset(
    datasource,
    name=u'dataset one',
    query=u'SELECT * FROM tg_user'
):
    dataset = model.DataSet(
        name=name,
        query=query,
        datasource=datasource,
        uid=randint(1, 100000)
    )
    model.DBSession.add(dataset)
    return dataset


def create_extraction_dataset(
        extraction,
        dataset,
        priority=0,
        join_type='left',
        join_self_col=None,
        join_other_col=None
):
    exd = model.ExtractionDataSet()
    exd.extraction = extraction
    exd.dataset = dataset
    exd.priority = priority
    exd.join_type = join_type
    exd.join_self_col = join_self_col
    exd.join_other_col = join_other_col
    model.DBSession.add(exd)
    return exd
