import logging
import asyncio
from typing import List
from src.domain.services import BrowserEngine

logger = logging.getLogger("flight_scraper")

def run_sync(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
    return loop.run_until_complete(coro)

class PyppeteerEngine(BrowserEngine):
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.page = None

    def start(self) -> None:
        logger.info("Initializing Pyppeteer (Puppeteer Python port)...")
        from pyppeteer import launch
        
        async def _start():
            self.browser = await launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            self.page = await self.browser.newPage()
            await self.page.setViewport({"width": 1280, "height": 800})
            await self.page.setUserAgent(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
        run_sync(_start())
        logger.info("Pyppeteer browser started successfully.")

    def navigate(self, url: str) -> None:
        if not self.page:
            raise RuntimeError("Browser session not started. Call start() first.")
        logger.info(f"Pyppeteer navigating to: {url}")
        
        async def _goto():
            await self.page.goto(url, {"waitUntil": "domcontentloaded", "timeout": 30000})
            
        run_sync(_goto())

    def get_title(self) -> str:
        if not self.page:
            return ""
        
        async def _title():
            return await self.page.title()
            
        try:
            return run_sync(_title())
        except Exception:
            return ""

    def get_body_text(self) -> str:
        if not self.page:
            return ""
            
        async def _body():
            return await self.page.evaluate("document.body.innerText")
            
        try:
            return run_sync(_body())
        except Exception:
            return ""

    def get_elements_text_by_xpath(self, xpath: str) -> List[str]:
        if not self.page:
            return []
            
        js_func = """(xpath) => {
            const result = [];
            const nodesSnapshot = document.evaluate(
                xpath, 
                document, 
                null, 
                XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, 
                null
            );
            for (let i = 0; i < nodesSnapshot.snapshotLength; i++) {
                const val = nodesSnapshot.snapshotItem(i).textContent;
                if (val) result.push(val.trim());
            }
            return result;
        }"""
        async def _eval():
            return await self.page.evaluate(js_func, xpath)
            
        try:
            return run_sync(_eval())
        except Exception as e:
            logger.error(f"Pyppeteer failed to fetch elements by xpath '{xpath}': {e}")
            return []

    def find_parent_with_xpath_child_text(self, child_xpath: str, target_xpath: str, max_depth: int = 10) -> str:
        if not self.page:
            return "N/A"
            
        js_func = """(childXpath, targetXpath, maxDepth) => {
            const child = document.evaluate(
                childXpath, 
                document, 
                null, 
                XPathResult.FIRST_ORDERED_NODE_TYPE, 
                null
            ).singleNodeValue;
            
            if (!child) return "N/A";
            
            let current = child;
            for (let i = 0; i < maxDepth; i++) {
                current = current.parentElement;
                if (!current) break;
                
                const target = document.evaluate(
                    targetXpath, 
                    current, 
                    null, 
                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                    null
                ).singleNodeValue;
                
                if (target) return target.textContent.trim();
            }
            return "N/A";
        }"""
        async def _eval():
            return await self.page.evaluate(js_func, child_xpath, target_xpath, max_depth)
            
        try:
            return str(run_sync(_eval()))
        except Exception as e:
            logger.error(f"Pyppeteer DOM parent tracing failed: {e}")
            return "N/A"

    def check_exists_by_xpath(self, xpath: str) -> bool:
        if not self.page:
            return False
            
        js_func = """(xpath) => {
            const element = document.evaluate(
                xpath, 
                document, 
                null, 
                XPathResult.FIRST_ORDERED_NODE_TYPE, 
                null
            ).singleNodeValue;
            return !!element;
        }"""
        async def _eval():
            return await self.page.evaluate(js_func, xpath)
            
        try:
            return bool(run_sync(_eval()))
        except Exception:
            return False

    def close(self) -> None:
        if self.browser:
            logger.info("Closing Pyppeteer browser...")
            async def _close():
                await self.browser.close()
            run_sync(_close())
            self.browser = None
            self.page = None
            logger.info("Pyppeteer terminated.")
