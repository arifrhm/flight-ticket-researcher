import pytest
import os
from typing import List
from src.domain.entities import FlightPrice
from src.domain.value_objects import Route
from src.domain.repositories import FlightRepository
from src.domain.services import FlightScraperService
from src.application.research_flights import ResearchFlightsUseCase

class MockScraperService(FlightScraperService):
    def __init__(self, stubbed_prices: List[FlightPrice]):
        self.stubbed_prices = stubbed_prices
        self.scraped_route = None
        self.scraped_dates = None

    def scrape_dates(self, route: Route, target_dates: List[str]) -> List[FlightPrice]:
        self.scraped_route = route
        self.scraped_dates = target_dates
        return self.stubbed_prices

class MockRepository(FlightRepository):
    def __init__(self):
        self.saved_prices = None

    async def save(self, prices: List[FlightPrice]) -> None:
        self.saved_prices = prices

class MockObservabilityManager:
    def __init__(self):
        self.session_started = False
        self.session_ended = False

    def start_session(self):
        self.session_started = True

    async def end_session(self):
        self.session_ended = True

@pytest.mark.asyncio
async def test_usecase_execution(tmp_path):
    stubbed = [
        FlightPrice(tanggal="2026-08-01", maskapai="Garuda", harga="IDR 1.200.000", status="Success")
    ]
    scraper = MockScraperService(stubbed)
    repo = MockRepository()
    obs = MockObservabilityManager()
    
    usecase = ResearchFlightsUseCase(
        scraper_service=scraper,
        repository=repo,
        observability_manager=obs
    )
    
    route = Route(dcity="PLM", acity="JKT")
    dates = ["2026-08-01"]
    report_file = os.path.join(tmp_path, "report.md")
    
    await usecase.execute(route, dates, report_file)
    
    # Assertions
    assert obs.session_started is True
    assert obs.session_ended is True
    assert scraper.scraped_route == route
    assert scraper.scraped_dates == dates
    assert repo.saved_prices == stubbed
    assert os.path.exists(report_file) is True
