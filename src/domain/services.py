from abc import ABC, abstractmethod
from typing import List
from src.domain.entities import FlightPrice
from src.domain.value_objects import Route

class BrowserEngine(ABC):
    @abstractmethod
    def start(self) -> None:
        """Starts the browser session."""

    @abstractmethod
    def navigate(self, url: str) -> None:
        """Navigates to the specified URL."""

    @abstractmethod
    def get_title(self) -> str:
        """Returns the current page title."""

    @abstractmethod
    def get_body_text(self) -> str:
        """Returns the page body text."""

    @abstractmethod
    def get_elements_text_by_xpath(self, xpath: str) -> List[str]:
        """Finds elements by XPath and returns their text contents."""

    @abstractmethod
    def find_parent_with_xpath_child_text(self, child_xpath: str, target_xpath: str, max_depth: int = 10) -> str:
        """Finds matching target text within parent elements up to max_depth."""

    @abstractmethod
    def check_exists_by_xpath(self, xpath: str) -> bool:
        """Checks if an element matching the XPath exists."""

    @abstractmethod
    def close(self) -> None:
        """Closes the browser session."""


class FlightScraperService(ABC):
    @abstractmethod
    def scrape_dates(self, route: Route, target_dates: List[str]) -> List[FlightPrice]:
        """
        Executes search scraping for a route across multiple target dates.
        
        Args:
            route (Route): Travel route value object (origin -> destination).
            target_dates (List[str]): List of target dates.
            
        Returns:
            List[FlightPrice]: List of scraped FlightPrice entities.
        """
