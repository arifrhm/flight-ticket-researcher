from abc import ABC, abstractmethod
from typing import List
from src.domain.entities import FlightPrice

class FlightRepository(ABC):
    @abstractmethod
    async def save(self, prices: List[FlightPrice]) -> None:
        """
        Asynchronously persists a list of FlightPrice entities to storage.
        
        Args:
            prices (List[FlightPrice]): List of flight price scan results.
        """
