import pytest
from app.services.airdrop_radar import normalize_address

def test_normalize_address():
    assert normalize_address("0x" + "A" * 40) == "0x" + "a" * 40

def test_invalid_address():
    with pytest.raises(ValueError):
        normalize_address("not-an-address")

def test_invalid_hex_address():
    with pytest.raises(ValueError):
        normalize_address("0x" + "g" * 40)

def test_address_whitespace_is_normalized():
    assert normalize_address("  0x" + "B" * 40 + "  ") == "0x" + "b" * 40
