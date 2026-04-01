import os
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from .base import IBrowser

class ChromeBrowser(IBrowser):
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None

    def start(self):
        opts = webdriver.ChromeOptions()
        if self.headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
        
        prof = os.path.join(os.getcwd(), "chrome_profile")
        opts.add_argument(f"user-data-dir={prof}")
        opts.add_argument("--profile-directory=Default")
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
        return self.driver

    def stop(self):
        if self.driver:
            self.driver.quit()
