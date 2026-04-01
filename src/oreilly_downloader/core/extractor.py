import time
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class ExtractorService:
    def __init__(self, browser):
        self.browser = browser
        self.driver = browser.driver

    def extract_title(self) -> str:
        selectors = [
            (By.ID, "videoTitle"),
            (By.CSS_SELECTOR, "h2.MuiTypography-h2"),
            (By.CSS_SELECTOR, "h1"),
            (By.CSS_SELECTOR, "[data-testid='title']"),
            (By.CSS_SELECTOR, ".chapter-title"),
            (By.TAG_NAME, "title"),
        ]
        for by, sel in selectors:
            try:
                el = self.driver.find_element(by, sel)
                title = el.text or el.get_attribute("textContent")
                if title:
                    return title.strip()
            except:
                pass
        return "Unknown Video"

    def extract_transcript(self):
        # Initial scroll to trigger lazy loading if needed
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(1)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        # Wait up to 10 seconds for either the transcript body OR the toggle button to appear
        try:
            WebDriverWait(self.driver, 10).until(
                lambda d: d.find_elements(
                    By.CSS_SELECTOR, "div[data-testid='transcript-body']"
                )
                or d.find_elements(
                    By.CSS_SELECTOR, "button[data-testid='transcript-toggle']"
                )
            )
        except TimeoutException:
            # If neither appear within 10 seconds, it's likely a video with no transcript
            return None

        transcript_visible = False
        try:
            containers = self.driver.find_elements(
                By.CSS_SELECTOR, "div[data-testid='transcript']"
            )
            if containers and containers[0].is_displayed():
                transcript_visible = True
        except:
            pass

        if not transcript_visible:
            try:
                toggle_btn = self.driver.find_element(
                    By.CSS_SELECTOR, "button[data-testid='transcript-toggle']"
                )
                if toggle_btn:
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", toggle_btn
                    )
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", toggle_btn)
                    time.sleep(
                        2
                    )  # Give more time for the transcript box to expand/animate open
            except Exception:
                pass

        try:
            # Re-fetch container and body and add an explicit wait for the body
            container = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[data-testid='transcript']")
                )
            )
            body = WebDriverWait(container, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[data-testid='transcript-body']")
                )
            )

            # Wait for the actual lines to render inside the body
            WebDriverWait(body, 5).until(
                lambda b: len(b.find_elements(By.CSS_SELECTOR, "button")) > 0
            )

            buttons = body.find_elements(By.CSS_SELECTOR, "button")
            lines = []
            for btn in buttons:
                try:
                    p_tags = btn.find_elements(By.TAG_NAME, "p")
                    if len(p_tags) >= 2:
                        timestamp = p_tags[0].text.strip()
                        text = p_tags[1].text.strip()
                        lines.append(f"[{timestamp}] {text}")
                except:
                    pass
            return "\n\n".join(lines) if lines else None
        except Exception:
            return None

    def extract_m3u8_url(self, video_url: str, timeout: int = 45) -> str:
        try:
            if video_url not in self.driver.current_url:
                print(f"  🚀 Loading video page: {video_url}")
                self.driver.get(video_url)
                time.sleep(5)

            script = """
            return window.performance.getEntriesByType("resource")
                .map(e => e.name)
                .filter(name => name.includes('.m3u8'));
            """
            urls = set()
            start_time = time.time()
            while time.time() - start_time < timeout:
                main_links = self.driver.execute_script(script)
                if main_links:
                    for link in main_links:
                        urls.add(link)
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    try:
                        self.driver.switch_to.frame(iframe)
                        iframe_links = self.driver.execute_script(script)
                        if iframe_links:
                            for link in iframe_links:
                                urls.add(link)
                    except:
                        pass
                    finally:
                        self.driver.switch_to.default_content()
                if urls:
                    url_list = list(urls)
                    return url_list[0]
                time.sleep(2)
            return None
        except Exception:
            return None

    def extract_course_structure(self, course_url: str):
        self.driver.get(course_url)
        time.sleep(5)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        script = r"""
        function cleanName(text) {
            let t = text.trim();
            t = t.replace(/Complete$/i, '');
            t = t.replace(/\d+[smh](\s+\d+[sm])?(\s*remaining)?\s*$/i, '');     
            return t.trim();
        }
        const allVideoLinks = document.querySelectorAll('a[href*="/videos/"][href*="/9780"]');
        const courseStructure = {};
        let currentModule = "Module Content";
        let currentLesson = "Introduction";
        allVideoLinks.forEach(link => {
            const url = link.href;
            const title = cleanName(link.textContent || "");
            let tempParent = link.parentElement;
            let moduleFound = false, lessonFound = false;
            for (let i = 0; i < 10 && tempParent; i++) {
                const prevElems = Array.from(tempParent.parentElement?.children || []);
                const currIdx = prevElems.indexOf(tempParent);
                for (let j = currIdx - 1; j >= 0; j--) {
                    const heading = prevElems[j].querySelector('h2, h3, h4, h5') || (prevElems[j].tagName.match(/H[2-5]/) ? prevElems[j] : null);
                    if (heading) {
                        const ht = cleanName(heading.textContent || "");        
                        if (ht.toLowerCase().includes('module') && !moduleFound) { 
                            if (currentModule !== ht) {
                                currentModule = ht;
                                currentLesson = "Introduction"; // Reset lesson on new module
                            }
                            moduleFound = true; 
                        }
                        else if (ht.toLowerCase().includes('lesson') && !lessonFound) { 
                            currentLesson = ht; 
                            lessonFound = true; 
                        }
                    }
                }
                tempParent = tempParent.parentElement;
            }
            if (!courseStructure[currentModule]) courseStructure[currentModule] = {};
            if (!courseStructure[currentModule][currentLesson]) courseStructure[currentModule][currentLesson] = [];
            courseStructure[currentModule][currentLesson].push({title: title, url: url});
        });
        return courseStructure;
        """
        return self.driver.execute_script(script)
