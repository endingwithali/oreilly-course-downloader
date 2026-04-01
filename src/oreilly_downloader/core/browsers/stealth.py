import os
import undetected_chromedriver as uc
from .base import IBrowser

class StealthChromeBrowser(IBrowser):
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None

    def start(self):
        print(f"🚀 Starting Stealth Chrome (Headless: {self.headless})...")
        opts = uc.ChromeOptions()
        if self.headless:
            opts.add_argument("--headless")
        prof = os.path.join(os.getcwd(), "browser_profile_stealth")
        
        self.driver = uc.Chrome(options=opts, user_data_dir=prof)
        return self.driver

    def stop(self):
        if self.driver:
            self.driver.quit()
