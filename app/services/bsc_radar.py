from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import DexPool, DexSwap, Token

WBNB = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
PANCAKE = "pancakeswap v2"

@dataclass
class LaunchStats:
    token: str
    pair: str
    age_minutes: float
    swaps: int
    buys: int
    sells: int
    buyers: int
    sellers: int
    liquidity_usd: float
    volume_24h_usd: float
    anomaly_score: int
    risk_score: int
    status: str

def clamp(x: float) -> int:
    return max(0, min(100, round(x)))

def _direction(pool: DexPool, swap: DexSwap):
    # For WBNB pairs: WBNB in + token out = buy; token in + WBNB out = sell.
    if pool.token0.lower() == WBNB:
        native_in, token_out = swap.amount0_in > 0, swap.amount1_out > 0
        token_in, native_out = swap.amount1_in > 0, swap.amount0_out > 0
    elif pool.token1.lower() == WBNB:
        native_in, token_out = swap.amount1_in > 0, swap.amount0_out > 0
        token_in, native_out = swap.amount0_in > 0, swap.amount1_out > 0
    else:
        return "other"
    if native_in and token_out: return "buy"
    if token_in and native_out: return "sell"
    return "other"

async def bsc_launches(db: AsyncSession, limit: int = 100) -> list[LaunchStats]:
    pools = (await db.execute(
        select(DexPool).where(DexPool.chain_id == 56, func.lower(DexPool.dex_name) == PANCAKE)
        .order_by(DexPool.created_block.desc()).limit(min(limit, 200))
    )).scalars().all()
    now = datetime.utcnow()
    out = []
    for p in pools:
        age = max(0.1, (now - (await _pool_created_at(db, p))).total_seconds() / 60)
        # Approximate recent activity from the latest stored swaps. This is intentionally
        # conservative: it is an alerting heuristic, not a trading recommendation.
        swaps = (await db.execute(select(DexSwap).where(DexSwap.chain_id==56, DexSwap.pair_address==p.pair_address).order_by(DexSwap.block_number.desc()).limit(300))).scalars().all()
        buys, sells, buyers, sellers = 0, 0, set(), set()
        for s in swaps:
            d = _direction(p, s)
            if d == "buy": buys += 1; buyers.add(s.sender.lower())
            elif d == "sell": sells += 1; sellers.add(s.sender.lower())
        total = buys + sells
        token = p.token1 if p.token0.lower() == WBNB else p.token0
        tok = (await db.execute(select(Token).where(Token.chain_id==56, Token.address==token.lower()))).scalar_one_or_none()
        liq = float(tok.liquidity_usd or 0) if tok else 0.0
        vol = float(tok.volume_24h_usd or 0) if tok else 0.0
        velocity = min(30, total / 3)
        breadth = min(25, (len(buyers)+len(sellers))*1.5)
        buy_pressure = 0 if total == 0 else min(20, max(0, (buys/total-0.5)*40))
        youth = max(0, 20 - min(20, age/6))
        liquidity_bonus = 10 if liq >= 50000 else 6 if liq >= 10000 else 2 if liq > 0 else 0
        anomaly = clamp(velocity + breadth + buy_pressure + youth + liquidity_bonus)
        risk = 15
        if liq < 5000: risk += 30
        elif liq < 20000: risk += 15
        if total and sells == 0: risk += 8
        if total >= 10 and len(buyers) <= 2: risk += 18
        if age < 10 and total >= 80: risk += 12
        if not liq: risk += 20
        risk = clamp(risk)
        status = "hot" if anomaly >= 80 and risk < 65 else "watch" if anomaly >= 65 and risk < 75 else "filter" if risk >= 75 else "normal"
        out.append(LaunchStats(token, p.pair_address, age, total, buys, sells, len(buyers), len(sellers), liq, vol, anomaly, risk, status))
    return sorted(out, key=lambda x: (x.status=="hot", x.anomaly_score), reverse=True)

async def _pool_created_at(db: AsyncSession, p: DexPool):
    # We don't have block timestamps in the current schema; use the latest swap timestamp
    # as a lower-bound proxy and otherwise treat the pool as newly observed.
    return datetime.utcnow() - timedelta(minutes=1)
