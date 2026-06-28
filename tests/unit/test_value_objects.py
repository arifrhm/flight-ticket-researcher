from src.domain.value_objects import Route, DateConfig

def test_route_to_upper():
    route = Route(dcity="plm", acity="vie")
    upper_route = route.to_upper()
    assert upper_route.dcity == "PLM"
    assert upper_route.acity == "VIE"

def test_date_config_formatting():
    date_cfg = DateConfig(year_month="2026-08", days=[1, 5, 12])
    formatted = date_cfg.get_formatted_dates()
    assert formatted == ["2026-08-01", "2026-08-05", "2026-08-12"]
