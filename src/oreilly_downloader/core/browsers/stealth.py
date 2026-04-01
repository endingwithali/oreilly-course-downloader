import os
import undetected_chromedriver as uc
from .base import IBrowser


class StealthChromeBrowser(IBrowser):
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None

    def _get_options(self):
        opts = uc.ChromeOptions()
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--start-maximized")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")

        # NOTE: Do NOT spoof the User-Agent or manually change blink features!
        # undetected_chromedriver patches the chromedriver binary directly.
        # Any manual JS/Argument overrides actually trigger Akamai/Cloudflare's advanced
        # anomaly detection because they look forced or mismatch the actual Chrome v146 engine.

        if self.headless:
            opts.add_argument("--headless=new")
        return opts

    def start(self):
        print(f"🚀 Starting True Stealth Chrome (Headless: {self.headless})...")
        prof = os.path.join(os.getcwd(), "browser_profile_stealth")

        try:
            self.driver = uc.Chrome(options=self._get_options(), user_data_dir=prof)
        except Exception as e:
            err_msg = str(e)
            if "supports Chrome version" in err_msg:
                import re

                match = re.search(r"Current browser version is (\d+)", err_msg)
                if match:
                    ver = int(match.group(1))
                    print(
                        f"⚠️ Chrome version mismatch. Retrying with driver version {ver}..."
                    )
                    self.driver = uc.Chrome(
                        options=self._get_options(),
                        user_data_dir=prof,
                        version_main=ver,
                    )
                else:
                    raise
            else:
                raise

        # Removing manual CDP Javascript injections. Akamai detects JS native code overrides!
        # undetected-chromedriver works best when left native.

        return self.driver

    def stop(self):
        if self.driver:
            self.driver.quit()
