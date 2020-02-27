from etl.tests.e2e import TestAsAdmin

class TestExtractions(TestAsAdmin):
    def setUp(self):
        self.driver = self.__class__.driver

    def test_extraction_creation(self):
        self.driver.get("http://127.0.0.1:8081")
        self.driver.find_element_by_css_selector("#button_new_extraction").click()
        new_extraction_box = self.driver.find_element_by_css_selector("#new_extraction_box")
        assert new_extraction_box.is_displayed(), new_extraction_box.is_displayed()

        new_extraction_input = self.driver.find_element_by_css_selector('input.new_extraction_input')
        new_extraction_input.clear()
        new_extraction_input.send_keys("Extraction 1 on products")
        new_extraction_input.submit()
        ok_message = self.driver.find_element_by_css_selector(".ok").text
        assert "New Extraction successfully created" == ok_message, ok_message



    def test_edit_extraction(self):
        self.driver.get("http://127.0.0.1:8081")
        self.driver.find_element_by_css_selector("#button_new_extraction").click()
        new_extraction_box = self.driver.find_element_by_css_selector("#new_extraction_box")
        assert new_extraction_box.is_displayed(), new_extraction_box.is_displayed()
    
    