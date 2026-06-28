import logging
import os
import asyncio
from typing import List, Any
from src.domain.entities import FlightPrice
from src.domain.repositories import FlightRepository
from src.infrastructure.config.pydantic_config import ScraperConfig

logger = logging.getLogger("flight_scraper")

class DuckDbFlightRepository(FlightRepository):
    def __init__(self, config: ScraperConfig):
        self.config = config

    def _get_connection(self, db_path: str) -> Any:
        try:
            import duckdb
        except ImportError:
            logger.error("DuckDB is not installed. Please run: pip install duckdb")
            raise RuntimeError("Missing dependency: duckdb")
            
        db_path = os.path.abspath(db_path)
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        logger.info(f"Connecting to DuckDB database: {db_path}")
        return duckdb.connect(db_path)

    def _init_schema(self, conn: Any) -> None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS flight_prices (
                tanggal VARCHAR,
                maskapai VARCHAR,
                harga VARCHAR,
                status VARCHAR
            )
        """)

    def _insert_records(self, conn: Any, prices: List[FlightPrice]) -> None:
        logger.info(f"Writing {len(prices)} records to DuckDB 'flight_prices' table...")
        for price in prices:
            conn.execute(
                "INSERT INTO flight_prices VALUES (?, ?, ?, ?)",
                (price.tanggal, price.maskapai, price.harga, price.status)
            )

    def _export_parquet(self, conn: Any, path: str) -> None:
        abs_path = os.path.abspath(path)
        directory = os.path.dirname(abs_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        logger.info(f"Exporting DuckDB table natively to Parquet: {abs_path}")
        conn.execute(f"COPY flight_prices TO '{abs_path}' (FORMAT PARQUET)")

    def _export_csv(self, conn: Any, path: str) -> None:
        abs_path = os.path.abspath(path)
        directory = os.path.dirname(abs_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        logger.info(f"Exporting DuckDB table natively to CSV: {abs_path}")
        conn.execute(f"COPY flight_prices TO '{abs_path}' (HEADER, DELIMITER ',')")

    async def save(self, prices: List[FlightPrice]) -> None:
        opts = self.config.storage_options.get("duckdb", {})
        db_path = opts.get("db_path", "results/flights.db")
        parquet_path = opts.get("export_parquet_path")
        csv_path = opts.get("export_csv_path")
        
        def _db_operations():
            conn = self._get_connection(db_path)
            try:
                self._init_schema(conn)
                self._insert_records(conn, prices)
                
                if parquet_path:
                    self._export_parquet(conn, parquet_path)
                if csv_path:
                    self._export_csv(conn, csv_path)
            finally:
                conn.close()
                logger.info("DuckDB database connection closed.")
                
        try:
            await asyncio.to_thread(_db_operations)
        except Exception as e:
            logger.error(f"DuckDB repository operations failed: {e}")
            raise
