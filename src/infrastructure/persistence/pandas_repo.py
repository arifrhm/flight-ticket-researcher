import logging
import os
import asyncio
from typing import List
from src.domain.entities import FlightPrice
from src.domain.repositories import FlightRepository
from src.infrastructure.config.pydantic_config import ScraperConfig

logger = logging.getLogger("flight_scraper")

class PandasFlightRepository(FlightRepository):
    def __init__(self, config: ScraperConfig):
        self.config = config

    async def save(self, prices: List[FlightPrice]) -> None:
        try:
            import pandas as pd
        except ImportError:
            logger.error("Pandas is not installed. Please run: pip install pandas")
            raise RuntimeError("Missing dependency: pandas")
            
        results = [
            {
                "Tanggal": price.tanggal,
                "Maskapai": price.maskapai,
                "Harga": price.harga,
                "Status": price.status
            }
            for price in prices
        ]
        
        opts = self.config.storage_options.get("pandas", {})
        filepath = opts.get("filepath", "results/prices.parquet")
        fmt = opts.get("format", "parquet").lower()
        
        filepath = os.path.abspath(filepath)
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            await asyncio.to_thread(os.makedirs, directory, exist_ok=True)
            
        df = pd.DataFrame(results)
        
        try:
            if fmt == "parquet":
                try:
                    await asyncio.to_thread(df.to_parquet, filepath, index=False)
                    logger.info(f"Flight results saved asynchronously via Pandas to Parquet: {filepath}")
                except ImportError:
                    logger.error("pyarrow or fastparquet is required for Parquet exports. Please run: pip install pyarrow")
                    raise
            elif fmt == "csv":
                await asyncio.to_thread(df.to_csv, filepath, index=False, encoding="utf-8")
                logger.info(f"Flight results saved asynchronously via Pandas to CSV: {filepath}")
            elif fmt in ("excel", "xlsx"):
                await asyncio.to_thread(df.to_excel, filepath, index=False)
                logger.info(f"Flight results saved asynchronously via Pandas to Excel: {filepath}")
            else:
                raise ValueError(f"Unsupported Pandas format: {fmt}")
        except Exception as e:
            logger.error(f"Failed to export via Pandas repository: {e}")
            raise
