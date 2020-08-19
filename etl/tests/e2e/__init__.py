from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import ui as ui
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from etl.tests import TestController, setup_app, load_app
from etl.model import DBSession
from etl.model.datasource import reset_cache
from tgext.pluggable import app_model
import transaction
from random import randint
from etl import model
import os

from gearbox.commands.serve import ServeCommand
from tg.util import Bunch

class TestE2e(object):
    @classmethod
    def setup_class(cls):
        cls.app = load_app('main', 'test_e2e.ini')
        setup_app('test_e2e.ini')

        # cmd = ServeCommand(Bunch(options=Bunch(debug=True, log_file=None, relative_plugins=False, verbose_level=1)), Bunch(verbose_level=2))
        # cmd.run(Bunch(app_name=None, args=[], config_file='test_e2e.ini', daemon=False, monitor_restart=False, pid_file=None, reload=False, reload_interval=1, server=None, server_name=None, set_group=None, set_user=None, show_status=False, stop_daemon=False))

        cat = app_model.Category(
            name='Default category 1'
        )
        DBSession.add(cat)

        ds = model.Datasource(
            name='default_ds',
            url=u'sqlite:///etl/tests/e2e/sales.db',
            uid=randint(1, 100000)
        )
        model.DBSession.add(ds)

        dataset1 = model.DataSet(
            name='products',
            query='SELECT * FROM products',
            datasource=ds,
            uid=randint(1, 100000)
        )
        model.DBSession.add(dataset1)

        dataset2 = model.DataSet(
            name='regions',
            query='SELECT * FROM regions',
            datasource=ds,
            uid=randint(1, 100000)
        )
        model.DBSession.add(dataset2)

        dataset3 = model.DataSet(
            name='sales',
            query='SELECT * FROM sales',
            datasource=ds,
            uid=randint(1, 100000)
        )
        model.DBSession.add(dataset3)

        dataset4 = model.DataSet(
            name='time',
            query='SELECT * FROM time',
            datasource=ds,
            uid=randint(1, 100000)
        )
        model.DBSession.add(dataset4)

        extraction = model.Extraction(
            name="Estrazione uno",
            category=cat,
            uid=randint(1, 100000)
        )
        model.DBSession.add(extraction)

        DBSession.flush()
        transaction.commit()

        # create a new Chrome session
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        cls.driver = webdriver.Chrome(chrome_options=options)
        cls.driver.implicitly_wait(30)
        cls.driver.maximize_window()

    @classmethod
    def teardown_class(cls):
        cls.driver.quit()
        os.remove(__file__.replace('__init__.py', 'testse2e.db'))

    
class TestAsAdmin(TestE2e):
    @classmethod
    def setup_class(cls):
        super(TestAsAdmin, cls).setup_class()

        cls.driver.get("http://127.0.0.1:8081")
        driverWait = ui.WebDriverWait(cls.driver, 10) # timeout after 10 seconds
 
        username = cls.driver.find_element_by_css_selector('input[name="login"]')
        password = cls.driver.find_element_by_css_selector('input[name="password"]')
        username.clear()
        password.clear()
        
        username.send_keys("admin")
        password.send_keys("adminpass")
        password.submit()
        warning = cls.driver.find_element_by_css_selector(".ok").text
        assert "Welcome back, admin!" == warning, warning
        
        # results = driverWait.until(lambda driverWait: driverWait.find_element_by_css_selector('.navbar'))
        # timeout = 5
        # try:
        #     import pdb
        #     pdb.set_trace()
        #     header_present = EC.presence_of_element_located((By.CLASS_NAME, 'nvbar'))
        #     WebDriverWait(self.driver, timeout).until(header_present)
        # except TimeoutException:
        #     print("Timed out waiting for page to load")
