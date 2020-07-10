"""This module contains the ``SeleniumRequest`` class"""

from scrapy import Request


class SeleniumRequest(Request):
    """Scrapy ``Request`` subclass providing additional arguments"""

    var_names = ["wait_time", "wait_until", "screenshot", "script"]

    def __init__(
        self,
        wait_time=None,
        wait_until=None,
        screenshot=False,
        script=None,
        *args,
        **kwargs,
    ):
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

        """

        self.wait_time = wait_time
        self.wait_until = wait_until
        self.screenshot = screenshot
        self.script = script

        super().__init__(*args, **kwargs)

        for name, value in zip(
            self.var_names, map(lambda x: getattr(self, x), self.var_names)
        ):
            if value:
                self.meta[name] = value

    def unpack_meta(self):
        for name in self.var_names:
            setattr(self, name, self.meta.get(name))
        return self
