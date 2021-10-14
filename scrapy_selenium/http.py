"""This module contains the ``SeleniumRequest`` class"""

from scrapy import Request


class SeleniumRequest(Request):
    """Scrapy ``Request`` subclass providing additional arguments"""

    def __init__(self, timeout=None, until=None, screenshot=False, script=None, *args, **kwargs):
        """Initialize a new selenium request

        Parameters
        ----------
        timeout: float
            The number of seconds to wait.
        until: method
            One of the "selenium.webdriver.support.expected_conditions". The response
            will be returned until the given condition is fulfilled.
        screenshot: bool
            If True, a screenshot of the page will be taken and the data of the screenshot
            will be returned in the response "meta" attribute.
        script: str
            JavaScript code to execute.

        """

        self.timeout = timeout
        self.until = until
        self.screenshot = screenshot
        self.script = script

        super().__init__(*args, **kwargs)
