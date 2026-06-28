from src.domain.entities import FlightPrice

def test_flight_price_success():
    price = FlightPrice(
        tanggal="2026-08-01",
        maskapai="Scoot",
        harga="US$477",
        status="Success"
    )
    assert price.is_successful() is True
    assert price.has_flights() is True

def test_flight_price_no_flights():
    price = FlightPrice(
        tanggal="2026-08-01",
        maskapai="N/A",
        harga="No Flights",
        status="No Flights"
    )
    assert price.is_successful() is False
    assert price.has_flights() is False

def test_flight_price_failed():
    price = FlightPrice(
        tanggal="2026-08-01",
        maskapai="N/A",
        harga="Failed",
        status="Failed"
    )
    assert price.is_successful() is False
    assert price.has_flights() is True  # Status is not "No Flights"
