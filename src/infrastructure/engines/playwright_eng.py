import logging
from typing import List
from playwright.sync_api import sync_playwright
from src.domain.services import BrowserEngine

logger = logging.getLogger("flight_scraper")

class PlaywrightEngine(BrowserEngine):
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self) -> None:
        logger.info("Initializing Playwright Chromium browser...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        
        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        self.page = self.context.new_page()
        logger.info("Playwright Chromium browser started successfully.")

    def navigate(self, url: str) -> None:
        if not self.page:
            raise RuntimeError("Browser session not started. Call start() first.")
        logger.info(f"Playwright navigating to: {url}")
        self.page.goto(url)

    def get_title(self) -> str:
        if not self.page:
            return ""
        return self.page.title()

    def get_body_text(self) -> str:
        if not self.page:
            return ""
        try:
            return self.page.locator("body").inner_text()
        except Exception:
            return ""

    def get_elements_text_by_xpath(self, xpath: str) -> List[str]:
        if not self.page:
            return []
        try:
            locators = self.page.locator(f"xpath={xpath}")
            count = locators.count()
            return [locators.nth(i).inner_text().strip() for i in range(count)]
        except Exception as e:
            logger.error(f"Playwright failed to fetch elements by xpath '{xpath}': {e}")
            return []

    def find_parent_with_xpath_child_text(self, child_xpath: str, target_xpath: str, max_depth: int = 10) -> str:
        if not self.page:
            return "N/A"
            
        js_func = """([childXpath, targetXpath, maxDepth]) => {
            const child = document.evaluate(childXpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (!child) return "N/A";
            let current = child;
            for (let i = 0; i < maxDepth; i++) {
                current = current.parentElement;
                if (!current) break;
                const target = document.evaluate(targetXpath, current, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                if (target) return target.textContent.trim();
            }
            return "N/A";
        }"""
        try:
            return str(self.page.evaluate(js_func, [child_xpath, target_xpath, max_depth]))
        except Exception as e:
            logger.error(f"Playwright DOM parent tracing failed: {e}")
            return "N/A"

    def check_exists_by_xpath(self, xpath: str) -> bool:
        if not self.page:
            return False
        try:
            return self.page.locator(f"xpath={xpath}").count() > 0
        except Exception:
            return False

    def close(self) -> None:
        logger.info("Closing Playwright sessions...")
        if self.page:
            self.page.close()
            self.page = None
        if self.context:
            self.context.close()
            self.context = None
        if self.browser:
            self.browser.close()
            self.browser = None
        if self.playwright:
            self.playwright.stop()
            self.playwright = None
        logger.info("Playwright session terminated.")
