from src.domain.repositories import FlightRepository
from src.infrastructure.config.pydantic_config import ScraperConfig

def get_repository(config: ScraperConfig) -> FlightRepository:
    """Resolves and instantiates the appropriate FlightRepository adapter based on configuration."""
    stype = config.storage_type.lower()
    
    if stype == "json":
        from src.infrastructure.persistence.json_repo import JsonFlightRepository
        return JsonFlightRepository(config)
        
    elif stype == "pandas":
        from src.infrastructure.persistence.pandas_repo import PandasFlightRepository
        return PandasFlightRepository(config)
        
    elif stype == "duckdb":
        from src.infrastructure.persistence.duckdb_repo import DuckDbFlightRepository
        return DuckDbFlightRepository(config)
        
    else:
        raise ValueError(f"Unsupported storage type: {config.storage_type}")
