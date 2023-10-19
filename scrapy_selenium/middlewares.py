from importlib import import_module
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.http import HtmlResponse
from .http import SeleniumRequest  # Assuming SeleniumRequest is in http.py in the same folder
import time

import logging

selenium_logger = logging.getLogger("selenium.webdriver.remote.remote_connection")
selenium_logger.setLevel(logging.INFO)


class SeleniumMiddleware:
    def __init__(
        self,
        driver_name,
        driver_executable_path,
        browser_executable_path,
        command_executor,
        driver_arguments,
    ):
        self.driver_name = driver_name
        self.driver_executable_path = driver_executable_path
        self.browser_executable_path = browser_executable_path
        self.command_executor = command_executor
        self.driver_arguments = driver_arguments
        self._initialize_driver()
        self.retry_count = 0

    def _initialize_driver(self):
        retries = 3
        for i in range(retries):
            try:
                webdriver_base_path = f"selenium.webdriver.{self.driver_name}"
                driver_klass_module = import_module(f"{webdriver_base_path}.webdriver")
                driver_klass = getattr(driver_klass_module, "WebDriver")
                driver_options_module = import_module(f"{webdriver_base_path}.options")
                driver_options_klass = getattr(driver_options_module, "Options")

                driver_options = driver_options_klass()
                if self.browser_executable_path:
                    driver_options.binary_location = self.browser_executable_path
                for argument in self.driver_arguments:
                    driver_options.add_argument(argument)

                driver_kwargs = {
                    "executable_path": self.driver_executable_path,
                    f"{self.driver_name}_options": driver_options,
                }

                if self.driver_executable_path is not None:
                    self.driver = driver_klass(**driver_kwargs)
                elif self.command_executor is not None:
                    self.driver = webdriver.Remote(
                        command_executor=self.command_executor, options=driver_options
                    )
                else:
                    if self.driver_name and self.driver_name.lower() == "chrome":
                        self.driver = webdriver.Chrome(
                            options=driver_options,
                            service=ChromeService(ChromeDriverManager().install()),
                        )
                break
            except WebDriverException:
                if i < retries - 1:  # not the last retry
                    print(
                        f"Encountered WebDriverException during driver initialization. Retrying... ({i+1})"
                    )
                    time.sleep(2**i)  # exponential backoff
                else:
                    print("Max retries reached. Could not initialize the driver.")
                    raise  # re-raise the exception

    @classmethod
    def from_crawler(cls, crawler):
        driver_name = crawler.settings.get("SELENIUM_DRIVER_NAME")
        driver_executable_path = crawler.settings.get("SELENIUM_DRIVER_EXECUTABLE_PATH")
        browser_executable_path = crawler.settings.get("SELENIUM_BROWSER_EXECUTABLE_PATH")
        command_executor = crawler.settings.get("SELENIUM_COMMAND_EXECUTOR")
        driver_arguments = crawler.settings.get("SELENIUM_DRIVER_ARGUMENTS")

        if not driver_name:
            raise NotConfigured("SELENIUM_DRIVER_NAME must be set")

        middleware = cls(
            driver_name,
            driver_executable_path,
            browser_executable_path,
            command_executor,
            driver_arguments,
        )

        crawler.signals.connect(middleware.spider_closed, signals.spider_closed)
        return middleware

    def process_request(self, request, spider):
        try:
            if not isinstance(request, SeleniumRequest):
                return None

            # OPENING WEBSITE
            self.driver.get(request.url)

            for cookie_name, cookie_value in request.cookies.items():
                self.driver.add_cookie({"name": cookie_name, "value": cookie_value})

            if request.wait_until:
                WebDriverWait(self.driver, request.wait_time).until(request.wait_until)

            if request.screenshot:
                request.meta["screenshot"] = self.driver.get_screenshot_as_png()

            if request.script:
                self.driver.execute_script(request.script)

            body = str.encode(self.driver.page_source)
            request.meta.update({"driver": self.driver})

            processed_request = HtmlResponse(
                self.driver.current_url, body=body, encoding="utf-8", request=request
            )
            self.retry_count = 0  # Reset the retry counter if successful
            return processed_request

        except WebDriverException:
            if self.retry_count < 3:  # Maximum retry limit
                print(
                    f"Encountered WebDriverException with {request.url}\nRetrying in {2 ** self.retry_count}s..."
                )
                self.retry_count += 1
                time.sleep(2**self.retry_count)  # Exponential backoff
                request.meta["retrying"] = True
                self._initialize_driver()
                return request
            else:
                self.retry_count = 0  # Reset the retry counter
                raise  # Reraise the exception if maximum retries reached

    def spider_closed(self):
        self.driver.quit()
