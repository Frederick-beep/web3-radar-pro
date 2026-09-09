from datetime import datetime
from scripts.seed_airdrops import parse_dt

def test_parse_dt_iso_z():
    assert parse_dt("2026-09-10T12:30:00Z") == datetime(2026, 9, 10, 12, 30)

def test_parse_dt_none():
    assert parse_dt(None) is None
