from selenium import webdriver

class TestLogin(object):
    def setUp(self):
        # create a new Chrome session
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(30)
        self.driver.maximize_window()
        # navigate to the application home page
        self.driver.get("http://127.0.0.1:8080")

    def test_login(self):
        # get the search textbox
        warning = self.driver.find_element_by_css_selector(".warning").text
        assert "The current user must have been authenticated" == warning, warning