from types import SimpleNamespace
from app.services.bsc_radar import _direction, WBNB

def pool(t0=WBNB, t1="0x"+"1"*40):
    return SimpleNamespace(token0=t0, token1=t1)
def swap(**kw):
    d=dict(amount0_in=0,amount1_in=0,amount0_out=0,amount1_out=0,sender="0x"+"2"*40)
    d.update(kw); return SimpleNamespace(**d)

def test_wbnb_buy_and_sell():
    p=pool()
    assert _direction(p,swap(amount0_in=10,amount1_out=5)) == "buy"
    assert _direction(p,swap(amount1_in=5,amount0_out=10)) == "sell"
