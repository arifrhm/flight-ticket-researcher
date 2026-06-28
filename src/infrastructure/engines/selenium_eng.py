import logging
from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from src.domain.services import BrowserEngine

logger = logging.getLogger("flight_scraper")

class SeleniumEngine(BrowserEngine):
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None

    def start(self) -> None:
        logger.info("Initializing Selenium Chrome WebDriver...")
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1280, 800)
        logger.info("Selenium Chrome WebDriver started successfully.")

    def navigate(self, url: str) -> None:
        if not self.driver:
            raise RuntimeError("Browser session not started. Call start() first.")
        self.driver.get(url)

    def get_title(self) -> str:
        if not self.driver:
            return ""
        return self.driver.title

    def get_body_text(self) -> str:
        if not self.driver:
            return ""
        try:
            return self.driver.find_element(By.TAG_NAME, "body").text
        except Exception:
            return ""

    def get_elements_text_by_xpath(self, xpath: str) -> List[str]:
        if not self.driver:
            return []
        elements = self.driver.find_elements(By.XPATH, xpath)
        return [el.text.strip() for el in elements if el.text]

    def find_parent_with_xpath_child_text(self, child_xpath: str, target_xpath: str, max_depth: int = 10) -> str:
        if not self.driver:
            return "N/A"
            
        elements = self.driver.find_elements(By.XPATH, child_xpath)
        if not elements:
            return "N/A"
            
        current = elements[0]
        for _ in range(max_depth):
            try:
                current = current.find_element(By.XPATH, "..")
                targets = current.find_elements(By.XPATH, target_xpath)
                if targets:
                    return targets[0].text.strip()
            except Exception:
                break
        return "N/A"

    def check_exists_by_xpath(self, xpath: str) -> bool:
        if not self.driver:
            return False
        return len(self.driver.find_elements(By.XPATH, xpath)) > 0

    def close(self) -> None:
        if self.driver:
            logger.info("Closing Selenium Chrome WebDriver...")
            self.driver.quit()
            self.driver = None
