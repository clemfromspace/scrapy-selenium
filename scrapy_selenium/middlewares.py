"""This module contains the ``SeleniumMiddleware`` scrapy middleware"""

from importlib import import_module
from typing import Iterable

from pylru import lrucache
from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.http import HtmlResponse
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from .http import SeleniumRequest


def on_driver_removed(proxy: str, driver: WebDriver):
    """
    Closes the webdriver when evicted from the cache.

    :param proxy: the proxy, not used
    :param driver: the driver being evicted
    """
    driver.quit()


class SeleniumMiddleware:
    """Scrapy middleware handling the requests using selenium"""
    # default proxy which is nop roxy at all
    default_proxy = ''

    def __init__(self, driver_name: str, driver_executable_path: str, driver_arguments: Iterable[str],
        browser_executable_path: str, max_concurrent_driver: int=8):
        """Initialize the selenium webdriver

        Parameters
        ----------
        driver_name: str
            The selenium ``WebDriver`` to use
        driver_executable_path: str
            The path of the executable binary of the driver
        driver_arguments: list
            A list of arguments to initialize the driver
        browser_executable_path: str
            The path of the executable binary of the browser
        max_concurrent_driver: str
            The maximal numnber of concurrent driver to be held
        """

        webdriver_base_path = f'selenium.webdriver.{driver_name}'

        driver_klass_module = import_module(f'{webdriver_base_path}.webdriver')
        driver_klass = getattr(driver_klass_module, 'WebDriver')

        driver_options_module = import_module(f'{webdriver_base_path}.options')
        driver_options_klass = getattr(driver_options_module, 'Options')

        driver_options = driver_options_klass()
        if browser_executable_path:
            driver_options.binary_location = browser_executable_path
        for argument in driver_arguments:
            driver_options.add_argument(argument)

        driver_kwargs = {
            'executable_path': driver_executable_path,
            f'{driver_name}_options': driver_options
        }

        def create_driver(proxy: str) -> WebDriver:
            """
            Creates a new driver, with optional proxy

            :param proxy: the proxy, which should be something like http://... or https://... or socks://
            :return: a webdriver created with the provided proxy
            """
            if proxy is not None and isinstance(proxy, str) and len(proxy) > 0:
                driver_kwargs[f'{driver_name}_options'].add_argument("--proxy-server={}".format(proxy))
            return driver_klass(**driver_kwargs)
        self.create_driver = create_driver
        self.drivers = lrucache(max_concurrent_driver, on_driver_removed)

    @classmethod
    def from_crawler(cls, crawler):
        """Initialize the middleware with the crawler settings"""

        driver_name = crawler.settings.get('SELENIUM_DRIVER_NAME')
        driver_executable_path = crawler.settings.get('SELENIUM_DRIVER_EXECUTABLE_PATH')
        browser_executable_path = crawler.settings.get('SELENIUM_BROWSER_EXECUTABLE_PATH')
        driver_arguments = crawler.settings.get('SELENIUM_DRIVER_ARGUMENTS')
        max_concurrent_driver = crawler.settings.get('SELENIUM_DRIVER_MAX_CONCURRENT')

        if not driver_name or not driver_executable_path:
            raise NotConfigured(
                'SELENIUM_DRIVER_NAME and SELENIUM_DRIVER_EXECUTABLE_PATH must be set'
            )

        middleware = cls(
            driver_name=driver_name,
            driver_executable_path=driver_executable_path,
            driver_arguments=driver_arguments,
            browser_executable_path=browser_executable_path,
            max_concurrent_driver=max_concurrent_driver
        )

        crawler.signals.connect(middleware.spider_closed, signals.spider_closed)

        return middleware

    def process_request(self, request, spider):
        """Process a request using the selenium driver if applicable"""

        if not isinstance(request, SeleniumRequest):
            return None

        # request a proxy:
        if request.meta.get('proxy', self.default_proxy) not in self.drivers:
            # this proxy is new, create a driver with this proxy
            driver = self.create_driver(request.meta.get('proxy', self.default_proxy))
            self.drivers[request.meta.get('proxy', self.default_proxy)] = driver
        return self.drivers[request.meta.get('proxy', self.default_proxy)]

        for cookie_name, cookie_value in request.cookies.items():
            driver.add_cookie(
                {
                    'name': cookie_name,
                    'value': cookie_value
                }
            )

        if request.wait_until:
            WebDriverWait(driver, request.wait_time).until(
                request.wait_until
            )

        if request.screenshot:
            request.meta['screenshot'] = driver.get_screenshot_as_png()

        if request.script:
            driver.execute_script(request.script)

        body = str.encode(driver.page_source)

        # Expose the driver via the "meta" attribute
        request.meta.update({'driver': driver})

        return HtmlResponse(
            driver.current_url,
            body=body,
            encoding='utf-8',
            request=request
        )

    def spider_closed(self):
        """Shutdown the driver when spider is closed"""

        self.drivers.clear()

