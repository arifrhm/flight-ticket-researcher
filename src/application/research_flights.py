import os
import logging
import asyncio
from typing import List, Any
from src.domain.value_objects import Route
from src.domain.repositories import FlightRepository
from src.domain.services import FlightScraperService

logger = logging.getLogger("flight_scraper")

class ResearchFlightsUseCase:
    def __init__(
        self, 
        scraper_service: FlightScraperService, 
        repository: FlightRepository, 
        observability_manager: Any = None
    ):
        """
        Application usecase to coordinate scraping usecase flow.
        
        Args:
            scraper_service (FlightScraperService): Scraping operations implementation.
            repository (FlightRepository): Data persistence implementation.
            observability_manager (Any): Monitor performance statistics.
        """
        self.scraper_service = scraper_service
        self.repository = repository
        self.observability_manager = observability_manager

    async def execute(self, route: Route, target_dates: List[str], report_path: str) -> None:
        if self.observability_manager:
            self.observability_manager.start_session()
            
        logger.info(f"Executing flight research usecase for route: {route.dcity} -> {route.acity}")
        
        # 1. Fetch flight data via Scraper adapter
        prices = self.scraper_service.scrape_dates(route, target_dates)
        
        # 2. Persist flight data via Repository adapter
        await self.repository.save(prices)
        
        # 3. Write user-facing markdown report
        if report_path:
            await self._generate_markdown_report(prices, route, target_dates, report_path)
            
        if self.observability_manager:
            await self.observability_manager.end_session()
            
        logger.info("Flight research usecase finished successfully.")

    async def _generate_markdown_report(
        self, 
        prices: List[Any], 
        route: Route, 
        target_dates: List[str], 
        filepath: str
    ) -> None:
        """Asynchronously writes a user-friendly Markdown report summary."""
        try:
            import aiofiles
            
            filepath = os.path.abspath(filepath)
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                await asyncio.to_thread(os.makedirs, directory, exist_ok=True)
                
            start_date = target_dates[0] if target_dates else "N/A"
            end_date = target_dates[-1] if target_dates else "N/A"
            
            async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                await f.write(f"# Laporan Harga Tiket Pesawat Termurah: {route.dcity.upper()} -> {route.acity.upper()}\n")
                await f.write(f"Periode: {start_date} s.d. {end_date}\n\n")
                await f.write("| Tanggal | Maskapai | Harga | Status |\n")
                await f.write("| --- | --- | --- | --- |\n")
                for price in prices:
                    await f.write(f"| {price.tanggal} | {price.maskapai} | {price.harga} | {price.status} |\n")
                    
            logger.info(f"Markdown report generated successfully at: {filepath}")
        except Exception as e:
            logger.error(f"Failed to generate Markdown report: {e}")
            raise
