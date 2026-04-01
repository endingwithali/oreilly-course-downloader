import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class AuthService:
    def __init__(self, browser):
        self.browser = browser
        self.driver = browser.driver

    def is_logged_in(self) -> bool:
        self.driver.get("https://learning.oreilly.com/home/")
        # check presence of user profile menu or standard login stuff
        time.sleep(3)
        try:
            # Basic heuristic: if the sign-in button exists, not logged in
            sign_in_btns = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'login') or contains(text(), 'Sign In')]")
            if sign_in_btns:
                return False
            return True
        except:
             return False

    def login(self, email: str, password: str) -> bool:
        if self.is_logged_in():
            print("✅ Already logged in using saved profile")
            return True
            
        print("🔐 Attempting automated login...")
        self.driver.get("https://learning.oreilly.com/accounts/login/")
        try:
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "id_email"))
            )
            email_field.send_keys(email)
            self.driver.find_element(By.ID, "id_password").send_keys(password)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            
            time.sleep(5)
            
            # Check for captchas or errors
            if self.is_logged_in():
                 return True
            return False
            
        except Exception as e:
            print(f"Login failed: {e}")
            return False
