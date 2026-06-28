import pytest
import time
import os
from typing import List, Dict
from src.domain.value_objects import Route
from src.domain.entities import FlightPrice
from src.domain.services import BrowserEngine
from src.infrastructure.config.pydantic_config import ScraperConfig, MonthConfig
from src.infrastructure.scrapers.trip_scraper import TripScraper
from src.infrastructure.monitoring.observability import ObservabilityManager

class MockBrowser(BrowserEngine):
    def __init__(self):
        self.navigated_urls = []
        self.started = False
        self.closed = False
        
        # Test custom fields
        self.title_value = "Palembang to Vienna flights - Trip.com"
        self.body_value = "Normal page body text"
        self.exists_xpaths = {}
        self.elements_xpaths = {}
        self.parent_xpath_value = "US$477"
        self.navigate_should_fail = False
        self.fail_count = 0
        
        self.navigate_calls = 0

    def start(self) -> None:
        self.started = True

    def navigate(self, url: str) -> None:
        self.navigate_calls += 1
        self.navigated_urls.append(url)
        if self.navigate_should_fail:
            raise RuntimeError("Mock network disconnect")
        if self.fail_count > 0:
            self.fail_count -= 1
            raise RuntimeError("Temporary network glitch")

    def get_title(self) -> str:
        return self.title_value

    def get_body_text(self) -> str:
        return self.body_value

    def get_elements_text_by_xpath(self, xpath: str) -> List[str]:
        return self.elements_xpaths.get(xpath, [])

    def find_parent_with_xpath_child_text(self, child_xpath: str, target_xpath: str, max_depth: int = 10) -> str:
        return self.parent_xpath_value

    def check_exists_by_xpath(self, xpath: str) -> bool:
        return self.exists_xpaths.get(xpath, False)

    def close(self) -> None:
        self.closed = True

def test_trip_scraper_success():
    config = ScraperConfig(
        max_retries=2,
        timeout_seconds=1,
        months=[MonthConfig(year_month="2026-08", days=[1])]
    )
    browser = MockBrowser()
    browser.elements_xpaths["//span[contains(@class, 'flights-name')]"] = ["Scoot"]
    browser.exists_xpaths["//span[contains(@class, 'flights-name')]"] = True
    
    scraper = TripScraper(config=config, engine=browser, observability=None)
    route = Route(dcity="PLM", acity="VIE")
    
    prices = scraper.scrape_dates(route, ["2026-08-01"])
    
    assert len(prices) == 1
    assert prices[0].tanggal == "2026-08-01"
    assert prices[0].maskapai == "Scoot"
    assert prices[0].harga == "US$477"
    assert prices[0].status == "Success"

def test_trip_scraper_anti_bot_retry(tmp_path):
    config = ScraperConfig(
        max_retries=2,
        timeout_seconds=1,
        months=[MonthConfig(year_month="2026-08", days=[1])]
    )
    browser = MockBrowser()
    browser.title_value = "Attention Required! | Cloudflare"
    
    metrics_file = os.path.join(tmp_path, "metrics.json")
    observability = ObservabilityManager(metrics_filepath=metrics_file)
    observability.start_session()
    
    scraper = TripScraper(config=config, engine=browser, observability=observability)
    route = Route(dcity="PLM", acity="VIE")
    
    call_count = 0
    def mock_trigger():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            return True  # cloudflare block (both in wait loop and in block execution check)
        browser.title_value = "Palembang to Vienna flights - Trip.com"
        browser.elements_xpaths["//span[contains(@class, 'flights-name')]"] = ["Austrian Airlines"]
        browser.exists_xpaths["//span[contains(@class, 'flights-name')]"] = True
        return False
        
    scraper._is_anti_bot_triggered = mock_trigger
    
    prices = scraper.scrape_dates(route, ["2026-08-01"])
    assert len(prices) == 1
    assert prices[0].maskapai == "Austrian Airlines"
    assert prices[0].status == "Success"

def test_trip_scraper_no_flights_detected(tmp_path):
    config = ScraperConfig(
        max_retries=1,
        timeout_seconds=1,
        months=[MonthConfig(year_month="2026-08", days=[1])]
    )
    browser = MockBrowser()
    browser.exists_xpaths[scraper_no_flight_xpath(browser)] = True
    
    metrics_file = os.path.join(tmp_path, "metrics.json")
    observability = ObservabilityManager(metrics_filepath=metrics_file)
    observability.start_session()
    
    scraper = TripScraper(config=config, engine=browser, observability=observability)
    route = Route(dcity="PLM", acity="VIE")
    
    prices = scraper.scrape_dates(route, ["2026-08-01"])
    assert len(prices) == 1
    assert prices[0].harga == "No Flights"
    assert prices[0].status == "No Flights"

def test_trip_scraper_exception_retry_and_fail(tmp_path):
    config = ScraperConfig(
        max_retries=2,
        timeout_seconds=1,
        months=[MonthConfig(year_month="2026-08", days=[1])]
    )
    browser = MockBrowser()
    browser.navigate_should_fail = True
    
    metrics_file = os.path.join(tmp_path, "metrics.json")
    observability = ObservabilityManager(metrics_filepath=metrics_file)
    observability.start_session()
    
    scraper = TripScraper(config=config, engine=browser, observability=observability)
    route = Route(dcity="PLM", acity="VIE")
    
    prices = scraper.scrape_dates(route, ["2026-08-01"])
    assert len(prices) == 1
    assert prices[0].harga == "Failed"
    assert prices[0].status == "Failed"

def test_trip_scraper_retry_empty_attempt():
    config = ScraperConfig(
        max_retries=2,
        timeout_seconds=1,
        months=[MonthConfig(year_month="2026-08", days=[1])]
    )
    browser = MockBrowser()
    
    # 1st attempt: elements don't exist -> triggers attempt empty log warn
    # 2nd attempt: elements exist!
    scraper = TripScraper(config=config, engine=browser, observability=None)
    route = Route(dcity="PLM", acity="VIE")
    
    call_count = 0
    def mock_exists(xpath):
        nonlocal call_count
        if "flights-name" in xpath:
            call_count += 1
            if call_count >= 2:
                browser.elements_xpaths["//span[contains(@class, 'flights-name')]"] = ["Singapore Airlines"]
                return True
        return False
        
    browser.check_exists_by_xpath = mock_exists
    
    prices = scraper.scrape_dates(route, ["2026-08-01"])
    assert len(prices) == 1
    assert prices[0].maskapai == "Singapore Airlines"
    assert prices[0].status == "Success"

def test_trip_scraper_timeout():
    # Use valid integer 1 for timeout_seconds to satisfy Pydantic
    config = ScraperConfig(
        max_retries=1,
        timeout_seconds=1,
        months=[MonthConfig(year_month="2026-08", days=[1])]
    )
    browser = MockBrowser()
    # Wait loop times out and returns False, leading to Failure
    
    scraper = TripScraper(config=config, engine=browser, observability=None)
    route = Route(dcity="PLM", acity="VIE")
    
    prices = scraper.scrape_dates(route, ["2026-08-01"])
    assert len(prices) == 1
    assert prices[0].status == "Failed"

def scraper_no_flight_xpath(browser):
    return (
        "//*[contains(text(), 'No flights') or "
        "contains(text(), 'No direct flights') or "
        "contains(text(), 'not find any flights')]"
    )
