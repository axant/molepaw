from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import ui as ui
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class TestE2e(object):
    def setUp(self):
        # create a new Chrome session
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(30)
        self.driver.maximize_window()
    
class TestAsAdmin(TestE2e):
    def setUp(self):
        super(TestAsAdmin, self).setUp()

        self.driver.get("http://127.0.0.1:8080")
        driverWait = ui.WebDriverWait(self.driver, 10) # timeout after 10 seconds
 
        username = self.driver.find_element_by_css_selector('input[name="login"]')
        password = self.driver.find_element_by_css_selector('input[name="password"]')
        username.clear()
        password.clear()
        
        username.send_keys("admin")
        password.send_keys("adminpass")
        password.submit()
        warning = self.driver.find_element_by_css_selector(".ok").text
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
