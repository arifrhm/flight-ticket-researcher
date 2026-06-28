import os
import json
import pytest
from pydantic import ValidationError
from src.infrastructure.config.pydantic_config import ScraperConfig

@pytest.mark.asyncio
async def test_scraper_config_loading_valid(tmp_path):
    config_data = {
        "engine_type": "selenium",
        "storage_type": "json",
        "dcity": "JKT",
        "acity": "SIN",
        "max_retries": 3,
        "timeout_seconds": 10,
        "months": [
            {"year_month": "2026-08", "days": [1, 2]}
        ]
    }
    
    filepath = os.path.join(tmp_path, "config.json")
    with open(filepath, "w") as f:
        json.dump(config_data, f)
        
    config = await ScraperConfig.load_from_json(filepath)
    assert config.engine_type == "selenium"
    assert config.dcity == "JKT"
    assert config.get_target_dates() == ["2026-08-01", "2026-08-02"]

@pytest.mark.asyncio
async def test_scraper_config_validation_error(tmp_path):
    # max_retries is 0, which violates ge=1
    invalid_data = {
        "engine_type": "selenium",
        "storage_type": "json",
        "max_retries": 0,
    }
    
    filepath = os.path.join(tmp_path, "invalid_config.json")
    with open(filepath, "w") as f:
        json.dump(invalid_data, f)
        
    with pytest.raises(ValidationError):
        await ScraperConfig.load_from_json(filepath)
