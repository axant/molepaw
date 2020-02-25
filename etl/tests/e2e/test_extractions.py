from etl.tests.e2e import TestAsAdmin

class TestExtractions(TestAsAdmin):
    def setUp(self):
        super(TestExtractions, self).setUp()

    def test_extraction(self):
        self.driver.find_element_by_css_selector("#button_new_extraction").click()
        new_extraction_box = self.driver.find_element_by_css_selector("#new_extraction_box")
        assert new_extraction_box.is_displayed(), new_extraction_box.is_displayed()
    
    def tearDown(self):
        # close the browser window
        self.driver.quit()