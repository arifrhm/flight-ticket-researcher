import os
import json
import pytest
import shutil
import duckdb
from src.domain.value_objects import Route
from src.domain.services import BrowserEngine
from src.infrastructure.config.pydantic_config import ScraperConfig, MonthConfig
from src.infrastructure.scrapers.trip_scraper import TripScraper
from src.infrastructure.persistence.duckdb_repo import DuckDbFlightRepository
from src.infrastructure.monitoring.observability import ObservabilityManager
from src.application.research_flights import ResearchFlightsUseCase

class FakeBrowserEngine(BrowserEngine):
    def __init__(self):
        self.started = False
        self.navigated_url = None
        self.closed = False

    def start(self) -> None:
        self.started = True

    def navigate(self, url: str) -> None:
        self.navigated_url = url

    def get_title(self) -> str:
        return "Cheap Flights from Palembang to Vienna - Trip.com"

    def get_body_text(self) -> str:
        return "Some page body mock text"

    def get_elements_text_by_xpath(self, xpath: str) -> list:
        if "flights-name" in xpath:
            return ["Scoot"]
        return []

    def find_parent_with_xpath_child_text(self, child_xpath: str, target_xpath: str, max_depth: int = 10) -> str:
        return "US$477"

    def check_exists_by_xpath(self, xpath: str) -> bool:
        if "flights-name" in xpath:
            return True
        return False

    def close(self) -> None:
        self.closed = True

@pytest.mark.asyncio
async def test_end_to_end_scraping_flow(tmp_path):
    # 1. Prepare configuration values
    config = ScraperConfig(
        engine_type="selenium",
        storage_type="duckdb",
        storage_options={
            "duckdb": {
                "db_path": os.path.join(tmp_path, "flights.db"),
                "export_parquet_path": os.path.join(tmp_path, "prices.parquet"),
                "export_csv_path": os.path.join(tmp_path, "prices.csv")
            }
        },
        metrics_file=os.path.join(tmp_path, "metrics.json"),
        dcity="PLM",
        acity="VIE",
        max_retries=1,
        timeout_seconds=2,
        months=[MonthConfig(year_month="2026-08", days=[1])]
    )
    
    # 2. Setup domain values
    route = Route(dcity=config.dcity, acity=config.acity).to_upper()
    target_dates = config.get_target_dates()
    
    # 3. Instantiate domain interfaces using fake browser engine
    engine = FakeBrowserEngine()
    observability = ObservabilityManager(metrics_filepath=config.metrics_file)
    repository = DuckDbFlightRepository(config=config)
    
    scraper_service = TripScraper(
        config=config,
        engine=engine,
        observability=observability
    )
    
    # 4. Inject into application usecase
    usecase = ResearchFlightsUseCase(
        scraper_service=scraper_service,
        repository=repository,
        observability_manager=observability
    )
    
    report_file = os.path.join(tmp_path, "report.md")
    
    # 5. Execute usecase
    await usecase.execute(route, target_dates, report_file)
    
    # 6. High-fidelity persistence E2E assertions
    assert engine.started is True
    assert engine.closed is True
    assert "ddate=2026-08-01" in engine.navigated_url
    
    # Assert database exists and contains the correct row
    db_file = config.storage_options["duckdb"]["db_path"]
    assert os.path.exists(db_file) is True
    
    # Perform manual DB assertion
    conn = duckdb.connect(db_file)
    rows = conn.execute("SELECT * FROM flight_prices").fetchall()
    conn.close()
    
    assert len(rows) == 1
    assert rows[0] == ("2026-08-01", "Scoot", "US$477", "Success")
    
    # Assert Parquet, CSV, Report, and Metrics files exist
    assert os.path.exists(config.storage_options["duckdb"]["export_parquet_path"]) is True
    assert os.path.exists(config.storage_options["duckdb"]["export_csv_path"]) is True
    assert os.path.exists(report_file) is True
    assert os.path.exists(config.metrics_file) is True
    
    # Read and verify metrics schema
    with open(config.metrics_file, "r") as f:
        metrics_data = json.load(f)
    assert len(metrics_data) == 1
    assert metrics_data[0]["successes"] == 1
    assert metrics_data[0]["success_rate_percent"] == 100.0
