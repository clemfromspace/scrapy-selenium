"""This module contains the test cases for the middlewares of the ``scrapy_selenium`` package"""
from shutil import which
from unittest import TestCase
from unittest.mock import patch

from scrapy import Request, Spider
from scrapy.exceptions import NotConfigured
from scrapy.settings import Settings
from scrapy.utils.test import get_crawler

from scrapy_selenium.http import SeleniumRequest
from scrapy_selenium.middlewares import SeleniumMiddleware


class SeleniumMiddlewareTestCase(TestCase):
    """Test case for the ``SeleniumMiddleware`` middleware"""

    def setUp(self):
        """Initialize the middleware"""
        self.settings = Settings({
            'SELENIUM_DRIVER_NAME': 'firefox',
            'SELENIUM_DRIVER_EXECUTABLE_PATH': which('geckodriver'),
            'SELENIUM_DRIVER_ARGUMENTS': ['-headless']
        })

        self.crawler = get_crawler(Spider, self.settings)
        self.spider = self.crawler._create_spider('foo')
        self.mw = SeleniumMiddleware.from_crawler(self.crawler)

    def tearDown(self):
        """Close the selenium webdriver"""
        self.mw.driver.quit()

    def test_from_crawler_method_exception(self):
        settings = Settings({'SELENIUM_DRIVER_ARGUMENTS': ['-headless']})
        crawler = get_crawler(Spider, settings)
        with self.assertRaisesRegex(NotConfigured, 'SELENIUM_DRIVER_NAME'):
            SeleniumMiddleware.from_crawler(crawler)

        settings.update({"SELENIUM_DRIVER_NAME": 'firefox'})
        crawler = get_crawler(Spider, settings)
        with self.assertRaisesRegex(NotConfigured, 'SELENIUM_DRIVER_EXECUTABLE_PATH'):
            SeleniumMiddleware.from_crawler(crawler)

        settings.update({'SELENIUM_DRIVER_EXECUTABLE_PATH': which('geckodriver')})
        crawler = get_crawler(Spider, settings)
        mw = SeleniumMiddleware.from_crawler(crawler)
        mw.driver.quit()

    def test_from_crawler_method_via_browser_executable_path(self):
        self.settings.update({'SELENIUM_DRIVER_NAME': 'firefox'})
        self.settings.update({'SELENIUM_BROWSER_EXECUTABLE_PATH': which('firefox')})
        crawler = get_crawler(Spider, self.settings)
        mw = SeleniumMiddleware.from_crawler(crawler)
        self.assertEqual(which('firefox'), mw.driver.binary._start_cmd)
        mw.driver.close()

    def test_from_crawler_method_should_initialize_the_driver(self):
        """Test that the ``from_crawler`` method should initialize the selenium driver"""

        crawler = get_crawler(Spider, self.settings)
        mw = SeleniumMiddleware.from_crawler(crawler)

        # The driver must be initialized
        self.assertIsNotNone(mw.driver)

        # We can now use the driver
        mw.driver.get('http://www.python.org')
        self.assertIn('Python', mw.driver.title)

        mw.driver.close()

    def test_from_crawler_method_should_initialize_the_grid(self):
        """"""
        self.settings.update({
            'SELENIUM_REMOTE_URL': 'http://localhost:4444/wd/hub'
        })
        crawler = get_crawler(Spider, self.settings)
        mw = SeleniumMiddleware.from_crawler(crawler)

        mw.driver.get('http://www.python.org')
        self.assertIn('Python', mw.driver.title)

        mw.driver.close()

    def test_spider_closed_should_close_the_driver(self):
        """Test that the ``spider_closed`` method should close the driver"""

        crawler = get_crawler(Spider, self.settings)
        mw = SeleniumMiddleware.from_crawler(crawler)

        with patch.object(mw.driver, 'quit') as mocked_quit:
            mw.spider_closed()

        mocked_quit.assert_called_once()

    def test_process_request_should_return_none_if_not_selenium_request(self):
        """Test that the ``process_request`` should return none if not selenium request"""

        scrapy_request = Request(url='http://not-an-url')

        self.assertIsNone(
            self.mw.process_request(
                request=scrapy_request,
                spider=None
            )
        )

    def test_process_request_should_return_a_response_if_selenium_request(self):
        """Test that the ``process_request`` should return a response if selenium request"""

        selenium_request = SeleniumRequest(url='http://www.python.org')

        html_response = self.mw.process_request(
            request=selenium_request,
            spider=None
        )

        # We have access to the driver on the response via the "meta"
        self.assertEqual(
            html_response.meta['driver'],
            self.mw.driver
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

        html_response = self.mw.process_request(
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

        html_response = self.mw.process_request(
            request=selenium_request,
            spider=None
        )

        self.assertEqual(
            html_response.selector.xpath('//title/text()').extract_first(),
            'scrapy_selenium'
        )
