import os
from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service
from .base import IBrowser

class FirefoxBrowser(IBrowser):
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None

    def start(self):
        opts = webdriver.FirefoxOptions()
        if self.headless:
            opts.add_argument("--headless")
        
        prof = os.path.join(os.getcwd(), "firefox_profile")
        opts.add_argument("-profile")
        opts.add_argument(prof)
        
        self.driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=opts)
        return self.driver

    def stop(self):
        if self.driver:
            self.driver.quit()
