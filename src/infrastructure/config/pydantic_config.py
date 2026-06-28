import json
import os
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class MonthConfig(BaseModel):
    year_month: str
    days: List[int]

class ScraperConfig(BaseModel):
    engine_type: str = "selenium"
    storage_type: str = "json"
    storage_options: Dict[str, Any] = Field(default_factory=dict)
    
    fastmcp: Dict[str, Any] = Field(default_factory=dict)
    selenium: Dict[str, Any] = Field(default_factory=dict)
    metrics_file: str = "results/metrics.json"
    
    dcity: str = "PLM"
    acity: str = "VIE"
    currency: str = "USD"
    locale: str = "en-XX"
    trip_type: str = "ow"
    cabin_class: str = "y"
    quantity: int = Field(default=1, ge=1)
    max_retries: int = Field(default=3, ge=1)
    timeout_seconds: int = Field(default=15, ge=1)
    months: List[MonthConfig] = Field(default_factory=list)

    @classmethod
    async def load_from_json(cls, filepath: str) -> "ScraperConfig":
        import aiofiles
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        
        async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
            content = await f.read()
            data = json.loads(content)
            
        return cls.model_validate(data)

    def get_target_dates(self) -> List[str]:
        dates = []
        for month in self.months:
            for day in month.days:
                dates.append(f"{month.year_month}-{day:02d}")
        return sorted(dates)
