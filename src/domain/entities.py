from dataclasses import dataclass

@dataclass
class FlightPrice:
    """Core domain entity representing a flight ticket price result."""
    tanggal: str      # ISO date (YYYY-MM-DD)
    maskapai: str     # Airline name
    harga: str        # Price formatted text (e.g. "US$477") or "No Flights"/"Failed"
    status: str       # Scan outcome status ("Success", "No Flights", "Failed")

    def is_successful(self) -> bool:
        return self.status == "Success"

    def has_flights(self) -> bool:
        return self.status != "No Flights"
