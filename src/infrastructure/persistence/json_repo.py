import logging
import os
import asyncio
from typing import List
from src.domain.entities import FlightPrice
from src.domain.repositories import FlightRepository
from src.infrastructure.config.pydantic_config import ScraperConfig

logger = logging.getLogger("flight_scraper")

class JsonFlightRepository(FlightRepository):
    def __init__(self, config: ScraperConfig):
        self.config = config

    async def save(self, prices: List[FlightPrice]) -> None:
        import aiofiles
        
        # Map domain entities to persistent dictionary structure
        results = [
            {
                "Tanggal": price.tanggal,
                "Maskapai": price.maskapai,
                "Harga": price.harga,
                "Status": price.status
            }
            for price in prices
        ]
        
        opts = self.config.storage_options.get("json", {})
        filepath = opts.get("filepath", "results/prices.json")
        serializer = opts.get("serializer", "json").lower()
        
        filepath = os.path.abspath(filepath)
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            await asyncio.to_thread(os.makedirs, directory, exist_ok=True)
            
        used_orjson = False
        if serializer == "orjson":
            try:
                import orjson
                data_bytes = await asyncio.to_thread(orjson.dumps, results, option=orjson.OPT_INDENT_2)
                async with aiofiles.open(filepath, "wb") as f:
                    await f.write(data_bytes)
                used_orjson = True
                logger.info(f"JSON results saved asynchronously via orjson to: {filepath}")
            except ImportError:
                logger.warning("orjson package is configured but not installed. Falling back to built-in json.")
            except Exception as e:
                logger.error(f"Error serialization with orjson: {e}. Falling back to built-in json.")
                
        if not used_orjson:
            import json
            try:
                data_str = await asyncio.to_thread(json.dumps, results, indent=4, ensure_ascii=False)
                async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                    await f.write(data_str)
                logger.info(f"JSON results saved asynchronously via built-in json to: {filepath}")
            except Exception as e:
                logger.error(f"Failed to save JSON results: {e}")
                raise
