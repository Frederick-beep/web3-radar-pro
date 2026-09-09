from app.main import app

def test_root_metadata():
    route = next(r for r in app.routes if getattr(r, "path", None) == "/")
    assert route is not None

def test_airdrop_routes_registered():
    paths = {getattr(r, "path", "") for r in app.routes}
    assert "/api/v2/airdrops" in paths
    assert "/api/v2/airdrops/calendar" in paths
    assert "/api/v2/airdrops/check-wallet" in paths
