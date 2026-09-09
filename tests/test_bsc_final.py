from app.services.bsc_final import clamp

def test_clamp():
    assert clamp(-1)==0
    assert clamp(50.4)==50
    assert clamp(120)==100
