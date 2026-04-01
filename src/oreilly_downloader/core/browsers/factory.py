from .base import IBrowser
from .stealth import StealthChromeBrowser
from .firefox import FirefoxBrowser
from .chrome import ChromeBrowser

class BrowserFactory:
    @staticmethod
    def create(browser_type: str, headless: bool = True) -> IBrowser:
        if browser_type == "stealth":
            return StealthChromeBrowser(headless=headless)
        elif browser_type == "firefox":
            return FirefoxBrowser(headless=headless)
        elif browser_type == "chrome":
            return ChromeBrowser(headless=headless)
        else:
            raise ValueError(f"Unknown browser type: {browser_type}")
