"""This module contains the test cases for the middlewares of the ``scrapy_selenium`` package"""

from unittest.mock import patch

from scrapy import Request
from scrapy.crawler import Crawler

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from scrapy_selenium.http import SeleniumRequest
from scrapy_selenium.middlewares import SeleniumMiddleware

from .test_cases import BaseScrapySeleniumTestCase


class SeleniumMiddlewareTestCase(BaseScrapySeleniumTestCase):
    """Test case for the ``SeleniumMiddleware`` middleware"""

    @classmethod
    def setUpClass(cls):
        """Initialize the middleware"""

        super().setUpClass()

        crawler = Crawler(
            spidercls=cls.spider_klass,
            settings=cls.settings
        )

        cls.selenium_middleware = SeleniumMiddleware.from_crawler(crawler)

    @classmethod
    def tearDownClass(cls):
        """Close the selenium webdriver"""

        super().tearDownClass()

        cls.selenium_middleware.driver.quit()

    def test_from_crawler_method_should_initialize_the_driver(self):
        """Test that the ``from_crawler`` method should initialize the selenium driver"""

        crawler = Crawler(
            spidercls=self.spider_klass,
            settings=self.settings
        )

        selenium_middleware = SeleniumMiddleware.from_crawler(crawler)

        # The driver must be initialized
        self.assertIsNotNone(selenium_middleware.driver)

        # We can now use the driver
        selenium_middleware.driver.get('http://www.python.org')
        self.assertIn('Python', selenium_middleware.driver.title)

        selenium_middleware.driver.close()

    def test_spider_closed_should_close_the_driver(self):
        """Test that the ``spider_closed`` method should close the driver"""

        crawler = Crawler(
            spidercls=self.spider_klass,
            settings=self.settings
        )

        selenium_middleware = SeleniumMiddleware.from_crawler(crawler)

        with patch.object(selenium_middleware.driver, 'quit') as mocked_quit:
            selenium_middleware.spider_closed()

        mocked_quit.assert_called_once()

    def test_process_request_should_return_none_if_not_selenium_request(self):
        """Test that the ``process_request`` should return none if not selenium request"""

        scrapy_request = Request(url='http://not-an-url')

        self.assertIsNone(
            self.selenium_middleware.process_request(
                request=scrapy_request,
                spider=None
            )
        )

    def test_process_request_should_return_a_response_if_selenium_request(self):
        """Test that the ``process_request`` should return a response if selenium request"""

        selenium_request = SeleniumRequest(url='http://www.python.org')

        html_response = self.selenium_middleware.process_request(
            request=selenium_request,
            spider=None
        )

        # We have access to the driver on the response via the "meta"
        self.assertEqual(
            html_response.meta['driver'],
            self.selenium_middleware.driver
        )

        # We also have access to the "selector" attribute on the response
        self.assertEqual(
            html_response.selector.xpath('//title/text()').extract_first(),
            'Welcome to Python.org'
        )

    def test_process_request_should_return_a_screenshot_if_screenshot_option(self):
        """Test that the ``process_request`` should return a response with a screenshot"""

        selenium_request = SeleniumRequest(
            url='http://www.python.org',
            screenshot=True
        )

        html_response = self.selenium_middleware.process_request(
            request=selenium_request,
            spider=None
        )

        self.assertIsNotNone(html_response.meta['screenshot'])

    def test_process_request_should_execute_script_if_script_option(self):
        """Test that the ``process_request`` should execute the script and return a response"""

        selenium_request = SeleniumRequest(
            url='http://www.python.org',
            script='document.title = "scrapy_selenium";'
        )

        html_response = self.selenium_middleware.process_request(
            request=selenium_request,
            spider=None
        )

        self.assertEqual(
            html_response.selector.xpath('//title/text()').extract_first(),
            'scrapy_selenium'
        )

    def test_process_request_should_execute_cb_selenium(self):
        """Test that the ``process_request`` should execute cb_selenium and return a response"""

        def cb_selenium(url, webdriver, query):
            wait = WebDriverWait(webdriver, timeout=10)

            webdriver.get(url)

            elt = wait.until(ec.visibility_of_element_located((By.ID, "id-search-field")))
            elt.send_keys(query + Keys.ENTER)

            wait.until(ec.visibility_of_element_located(
                (By.XPATH, "//ul[@class='list-recent-events menu']")
            ))

        selenium_request = SeleniumRequest(
            url='http://www.python.org',
            cb_selenium=cb_selenium,
            cb_selenium_kwargs={"query": "python"}
        )

        html_response = self.selenium_middleware.process_request(
            request=selenium_request,
            spider=None
        )

        titles_xpath = "//ul[@class='list-recent-events menu']/li/h3/a/text()"
        self.assertIn(
            "python",
            html_response.selector.xpath(titles_xpath).extract_first().lower()
        )
