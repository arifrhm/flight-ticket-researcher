import os
import argparse
import asyncio

# DDD Imports
from src.domain.value_objects import Route
from src.application.research_flights import ResearchFlightsUseCase

# Infrastructure Imports (Config, Scrapers, Persistences, Monitoring, Engines)
from src.infrastructure.config.pydantic_config import ScraperConfig
from src.infrastructure.monitoring.logger import setup_logger
from src.infrastructure.monitoring.observability import ObservabilityManager
from src.infrastructure.persistence import get_repository
from src.infrastructure.scrapers.trip_scraper import TripScraper

def get_engine(config: ScraperConfig):
    engine_type = config.engine_type.lower()
    
    if engine_type == "selenium":
        from src.infrastructure.engines.selenium_eng import SeleniumEngine
        headless = config.selenium.get("headless", True)
        return SeleniumEngine(headless=headless)
        
    elif engine_type == "playwright":
        from src.infrastructure.engines.playwright_eng import PlaywrightEngine
        headless = config.selenium.get("headless", True)
        return PlaywrightEngine(headless=headless)
        
    elif engine_type == "puppeteer" or engine_type == "pyppeteer":
        from src.infrastructure.engines.puppeteer_eng import PyppeteerEngine
        headless = config.selenium.get("headless", True)
        return PyppeteerEngine(headless=headless)
        
    elif engine_type == "fastmcp":
        from src.infrastructure.engines.fastmcp_eng import FastMcpEngine
        server_url = config.fastmcp.get("url")
        auth_token = config.fastmcp.get("token")
        if not server_url or not auth_token:
            raise ValueError("FastMCP configuration requires 'url' and 'token' keys in config.json.")
        return FastMcpEngine(server_url=server_url, auth_token=auth_token)
        
    else:
        raise ValueError(f"Unsupported browser engine type: {config.engine_type}")

async def run_orchestration(args: argparse.Namespace) -> None:
    # 1. Setup Logging (infra concern)
    logger = setup_logger(log_file=args.log_file)
    logger.info("Initializing DDD flight ticket research orchestration...")

    try:
        # 2. Load Configuration (infra concern)
        config_path = os.path.abspath(args.config)
        logger.info(f"Loading settings asynchronously from: {config_path}")
        config = await ScraperConfig.load_from_json(config_path)

        # 3. Translate Config to Pure Domain Values (domain concern)
        route = Route(dcity=config.dcity, acity=config.acity).to_upper()
        target_dates = config.get_target_dates()

        # 4. Instantiate Infrastructure Adapters (infra concern)
        engine = get_engine(config)
        repository = get_repository(config)
        observability = ObservabilityManager(metrics_filepath=config.metrics_file)
        
        scraper_service = TripScraper(
            config=config, 
            engine=engine, 
            observability=observability
        )

        # 5. Inject dependencies into Application Use Case (application concern)
        usecase = ResearchFlightsUseCase(
            scraper_service=scraper_service,
            repository=repository,
            observability_manager=observability
        )

        # 6. Execute Application Use Case
        await usecase.execute(
            route=route, 
            target_dates=target_dates, 
            report_path=args.output_report
        )

        logger.info("DDD orchestration completed successfully.")

    except Exception as e:
        logger.exception(f"Fatal error occurred during DDD scraper execution: {e}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Flight Price Scraper DDD Entrypoint")
    parser.add_argument(
        "--config", 
        default="config.json", 
        help="Path to the config.json configuration file."
    )
    parser.add_argument(
        "--output-json", 
        default="results/prices.json", 
        help="Path where output JSON should be saved."
    )
    parser.add_argument(
        "--output-report", 
        default="results/prices_report.md", 
        help="Path where output Markdown report should be saved."
    )
    parser.add_argument(
        "--log-file", 
        default="results/scraper.log", 
        help="Path to store log files."
    )
    args = parser.parse_args()

    # Launch CLI orchestrator inside async event loop
    asyncio.run(run_orchestration(args))

if __name__ == "__main__":
    main()
