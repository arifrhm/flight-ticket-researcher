import os
import json
import pytest
import pandas as pd
from src.domain.entities import FlightPrice
from src.infrastructure.config.pydantic_config import ScraperConfig
from src.infrastructure.persistence import get_repository
from src.infrastructure.persistence.json_repo import JsonFlightRepository
from src.infrastructure.persistence.pandas_repo import PandasFlightRepository

def test_get_repository_resolver():
    # test duckdb resolution
    config_dd = ScraperConfig(storage_type="duckdb")
    repo = get_repository(config_dd)
    assert repo.__class__.__name__ == "DuckDbFlightRepository"
    
    # test json resolution
    config_json = ScraperConfig(storage_type="json")
    repo = get_repository(config_json)
    assert repo.__class__.__name__ == "JsonFlightRepository"
    
    # test pandas resolution
    config_pandas = ScraperConfig(storage_type="pandas")
    repo = get_repository(config_pandas)
    assert repo.__class__.__name__ == "PandasFlightRepository"
    
    # test invalid
    config_invalid = ScraperConfig(storage_type="invalid")
    with pytest.raises(ValueError):
        get_repository(config_invalid)

@pytest.mark.asyncio
async def test_json_flight_repository_save(tmp_path):
    filepath = os.path.join(tmp_path, "prices.json")
    config = ScraperConfig(
        storage_type="json",
        storage_options={
            "json": {
                "filepath": filepath,
                "serializer": "json"
            }
        }
    )
    
    prices = [
        FlightPrice(tanggal="2026-08-01", maskapai="Scoot", harga="US$477", status="Success")
    ]
    
    repo = JsonFlightRepository(config)
    await repo.save(prices)
    
    assert os.path.exists(filepath) is True
    with open(filepath, "r") as f:
        data = json.load(f)
        
    assert len(data) == 1
    assert data[0]["Tanggal"] == "2026-08-01"
    assert data[0]["Maskapai"] == "Scoot"
    assert data[0]["Harga"] == "US$477"
    assert data[0]["Status"] == "Success"

@pytest.mark.asyncio
async def test_pandas_flight_repository_save(tmp_path):
    parquet_path = os.path.join(tmp_path, "prices.parquet")
    csv_path = os.path.join(tmp_path, "prices.csv")
    
    # Parquet test
    config_parquet = ScraperConfig(
        storage_type="pandas",
        storage_options={
            "pandas": {
                "filepath": parquet_path,
                "format": "parquet"
            }
        }
    )
    repo_parquet = PandasFlightRepository(config_parquet)
    prices = [
        FlightPrice(tanggal="2026-08-01", maskapai="Scoot", harga="US$477", status="Success")
    ]
    await repo_parquet.save(prices)
    assert os.path.exists(parquet_path) is True
    
    df = pd.read_parquet(parquet_path)
    assert len(df) == 1
    assert df.iloc[0]["Maskapai"] == "Scoot"
    
    # CSV test
    config_csv = ScraperConfig(
        storage_type="pandas",
        storage_options={
            "pandas": {
                "filepath": csv_path,
                "format": "csv"
            }
        }
    )
    repo_csv = PandasFlightRepository(config_csv)
    await repo_csv.save(prices)
    assert os.path.exists(csv_path) is True
    
    df_csv = pd.read_csv(csv_path)
    assert len(df_csv) == 1
    assert df_csv.iloc[0]["Harga"] == "US$477"
