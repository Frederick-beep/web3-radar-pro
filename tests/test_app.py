from app.main import app

def test_root_metadata():
    route = next(r for r in app.routes if getattr(r, "path", None) == "/")
    assert route is not None

def test_airdrop_routes_registered():
    paths = {getattr(r, "path", "") for r in app.routes}
    assert "/api/v2/airdrops" in paths
    assert "/api/v2/airdrops/calendar" in paths
    assert "/api/v2/airdrops/check-wallet" in paths

def test_app_version_and_ui_marker():
    from app.main import APP_VERSION
    assert APP_VERSION == "5.4.0"
    text = open("frontend/app.js", encoding="utf-8").read()
    assert "BSC 热门新币" in text
    assert "Airdrop opportunities" in text
