from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class Route:
    """Value object representing the travel route."""
    dcity: str
    acity: str

    def to_upper(self) -> "Route":
        return Route(self.dcity.upper(), self.acity.upper())

@dataclass(frozen=True)
class DateConfig:
    """Value object representing target months and dates."""
    year_month: str
    days: List[int]

    def get_formatted_dates(self) -> List[str]:
        dates = []
        for day in self.days:
            dates.append(f"{self.year_month}-{day:02d}")
        return dates
