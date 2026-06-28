import time
import logging
from typing import List, Dict, Optional, Any

from src.domain.services import FlightScraperService, BrowserEngine
from src.domain.entities import FlightPrice
from src.domain.value_objects import Route
from src.infrastructure.config.pydantic_config import ScraperConfig

logger = logging.getLogger("flight_scraper")

class TripScraper(FlightScraperService):
    def __init__(self, config: ScraperConfig, engine: BrowserEngine, observability: Any = None):
        """
        Scraper implementation for Trip.com.
        
        Args:
            config (ScraperConfig): Configuration model.
            engine (BrowserEngine): Browser driver adapter.
            observability (Any): Observability telemetry tracker.
        """
        self.config = config
        self.engine = engine
        self.observability = observability
        self.no_flight_xpath = (
            "//*[contains(text(), 'No flights') or "
            "contains(text(), 'No direct flights') or "
            "contains(text(), 'not find any flights')]"
        )

    def _wait_until_loaded(self) -> bool:
        start_time = time.time()
        timeout = self.config.timeout_seconds
        
        while time.time() - start_time < timeout:
            if self._is_anti_bot_triggered():
                return True
            if self.engine.check_exists_by_xpath("//span[contains(@class, 'flights-name')]"):
                return True
            if self.engine.check_exists_by_xpath(self.no_flight_xpath):
                return True
            time.sleep(0.5)
            
        return False

    def _build_url(self, route: Route, date: str) -> str:
        return (
            f"https://www.trip.com/flights/showfarefirst?"
            f"dcity={route.dcity.lower()}&"
            f"acity={route.acity.lower()}&"
            f"ddate={date}&"
            f"triptype={self.config.trip_type}&"
            f"class={self.config.cabin_class}&"
            f"quantity={self.config.quantity}&"
            f"locale={self.config.locale}&"
            f"curr={self.config.currency}"
        )

    def _is_anti_bot_triggered(self) -> bool:
        title = self.engine.get_title().lower()
        body_text = self.engine.get_body_text().lower()
        anti_bot_keywords = ["cloudflare", "attention required", "captcha", "verify you are human"]
        return any(kw in title for kw in anti_bot_keywords) or any(kw in body_text for kw in anti_bot_keywords)

    def _try_extract_cheapest_flight(self) -> Optional[Dict[str, str]]:
        airline_spans = self.engine.get_elements_text_by_xpath("//span[contains(@class, 'flights-name')]")
        if not airline_spans:
            return None
            
        airline_name = airline_spans[0]
        price_text = self.engine.find_parent_with_xpath_child_text(
            child_xpath="//span[contains(@class, 'flights-name')]",
            target_xpath=".//span[contains(@class, 'o-price-flight')]",
            max_depth=10
        )
        return {"airline": airline_name, "price": price_text}

    def _scrape_single_date(self, route: Route, date: str) -> FlightPrice:
        url = self._build_url(route, date)
        query_start_time = time.time()
        anti_bot_hit = False
        
        for attempt in range(1, self.config.max_retries + 1):
            try:
                self.engine.navigate(url)
                self._wait_until_loaded()
                time.sleep(2)
                
                # 1. Anti-bot checks
                if self._is_anti_bot_triggered():
                    logger.warning(f"Attempt {attempt}: Anti-bot block encountered for date {date}!")
                    anti_bot_hit = True
                    time.sleep(10)
                    continue
                    
                # 2. Extract flight card info
                flight_info = self._try_extract_cheapest_flight()
                if flight_info:
                    logger.info(f" -> Success: {flight_info['airline']} | {flight_info['price']}")
                    duration = time.time() - query_start_time
                    if self.observability:
                        self.observability.record_query("Success", duration, anti_bot_hit=anti_bot_hit)
                    return FlightPrice(
                        tanggal=date,
                        maskapai=flight_info["airline"],
                        harga=flight_info["price"],
                        status="Success"
                    )
                    
                # 3. Check for No Flights indicators
                if self.engine.check_exists_by_xpath(self.no_flight_xpath):
                    logger.info(" -> No flights found for this date.")
                    duration = time.time() - query_start_time
                    if self.observability:
                        self.observability.record_query("No Flights", duration, anti_bot_hit=anti_bot_hit)
                    return FlightPrice(
                        tanggal=date,
                        maskapai="N/A",
                        harga="No Flights",
                        status="No Flights"
                    )
                    
                logger.warning(f"Attempt {attempt} did not find results or no-flights indicators.")
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"Attempt {attempt} encountered exception: {e}")
                time.sleep(3)
                
        # Handle failures
        logger.error(f"Failed to retrieve flight prices for {date} after {self.config.max_retries} attempts.")
        duration = time.time() - query_start_time
        if self.observability:
            self.observability.record_query("Failed", duration, anti_bot_hit=anti_bot_hit)
        return FlightPrice(
            tanggal=date,
            maskapai="N/A",
            harga="Failed",
            status="Failed"
        )

    def scrape_dates(self, route: Route, target_dates: List[str]) -> List[FlightPrice]:
        results: List[FlightPrice] = []
        
        logger.info(f"Starting TripScraper for {len(target_dates)} target dates...")
        self.engine.start()
        
        try:
            for idx, date in enumerate(target_dates):
                logger.info(f"[{idx+1}/{len(target_dates)}] Scraping date: {date}")
                res = self._scrape_single_date(route, date)
                results.append(res)
                
                # Polite spacing delay between dates
                time.sleep(3)
        finally:
            logger.info("Stopping browser session...")
            self.engine.close()
            
        return results
