"""This module contains the ``SeleniumRequest`` class"""

from scrapy import Request


class SeleniumRequest(Request):
    """Scrapy ``Request`` subclass providing additional arguments"""

    def __init__(self, wait_time=None, wait_until=None, screenshot=False,
        script=None, cb_selenium=None, cb_selenium_kwargs=None, *args, **kwargs):
        """Initialize a new selenium request

        Parameters
        ----------
        wait_time: int
            The number of seconds to wait.
        wait_until: method
            One of the "selenium.webdriver.support.expected_conditions". The response
            will be returned until the given condition is fulfilled.
        screenshot: bool
            If True, a screenshot of the page will be taken and the data of the screenshot
            will be returned in the response "meta" attribute.
        script: str
            JavaScript code to execute.
        cb_selenium: method
            Selenium handler which contains webdriver actions leading to the expected
            state of the web page. The handler takes url, webdriver and custom arguments if needed
            `cb_selenium(url, webdriver, arg1, arg2)`.
        cb_selenium_kwargs: dict
            Keywords arguments for the selenium callback `cb_selenium`.

        """

        self.wait_time = wait_time
        self.wait_until = wait_until
        self.screenshot = screenshot
        self.script = script
        self.cb_selenium = cb_selenium
        self.cb_selenium_kwargs = cb_selenium_kwargs

        super().__init__(*args, **kwargs)
