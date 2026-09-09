from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import DexPool, DexSwap, Token, ContractScan, Signal
from app.services.bsc_radar import _direction, WBNB

@dataclass
class FinalLaunch:
    token: str
    pair: str
    dex: str
    age_minutes: float
    swaps_5m: int
    buys_5m: int
    sells_5m: int
    buyers_5m: int
    sellers_5m: int
    buy_pressure: float
    liquidity_usd: float
    volume_24h_usd: float
    risk_score: int
    risk_level: str
    anomaly_score: int
    status: str
    reasons: list[str]

    def dict(self): return asdict(self)

def clamp(v: float) -> int: return max(0, min(100, round(v)))

def _risk_adjustment(scan: ContractScan | None) -> tuple[int,str,list[str]]:
    if not scan: return 20, "unknown", ["contract scan pending"]
    return int(scan.risk_score), scan.risk_level, []

async def final_bsc_launches(db: AsyncSession, limit: int = 100) -> list[FinalLaunch]:
    pools=(await db.execute(select(DexPool).where(DexPool.chain_id==56).order_by(DexPool.created_block.desc()).limit(min(limit*3,300)))).scalars().all()
    now=datetime.now(timezone.utc).replace(tzinfo=None)
    result=[]
    for p in pools:
        token=p.token1 if p.token0.lower()==WBNB else p.token0 if p.token1.lower()==WBNB else None
        if not token: continue
        tok=(await db.execute(select(Token).where(Token.chain_id==56, Token.address==token.lower()))).scalar_one_or_none()
        created=tok.first_seen_at if tok else now
        age=max(0.1,(now-created).total_seconds()/60)
        # Keep the hot window intentionally small: this is a new-token radar, not a generic DEX screen.
        swaps=(await db.execute(select(DexSwap).where(DexSwap.chain_id==56,DexSwap.pair_address==p.pair_address).order_by(DexSwap.block_number.desc()).limit(1000))).scalars().all()
        # We do not fabricate timestamps. With block-only swap records, use a bounded latest-event sample.
        recent=swaps[:150]
        buys=sells=0; buyers=set(); sellers=set()
        for s in recent:
            d=_direction(p,s)
            if d=='buy': buys+=1; buyers.add(s.sender.lower())
            elif d=='sell': sells+=1; sellers.add(s.sender.lower())
        total=buys+sells
        pressure=(buys/total*100) if total else 0
        risk_row=(await db.execute(select(ContractScan).where(ContractScan.chain_id==56,ContractScan.token_address==token.lower()))).scalar_one_or_none()
        risk,level,risk_notes=_risk_adjustment(risk_row)
        liq=float(tok.liquidity_usd or 0) if tok else 0
        vol=float(tok.volume_24h_usd or 0) if tok else 0
        velocity=min(30,total/3)
        breadth=min(25,(len(buyers)+len(sellers))*1.4)
        pressure_score=min(20,max(0,(pressure-50)*0.4))
        youth=max(0,20-min(20,age/3))
        liq_score=10 if liq>=50000 else 7 if liq>=20000 else 4 if liq>=5000 else 0
        anomaly=clamp(velocity+breadth+pressure_score+youth+liq_score)
        reasons=[]
        if age<=15: reasons.append('very early launch')
        if buys>sells and buys>=10: reasons.append('buy flow dominates')
        if len(buyers)>=10: reasons.append('broad buyer participation')
        if liq>=20000: reasons.append('meaningful tracked liquidity')
        if risk>=75: reasons.append('high contract risk')
        if not risk_row: reasons.append('security scan pending')
        status='hot' if anomaly>=80 and risk<55 else 'watch' if anomaly>=65 and risk<75 else 'filter' if risk>=75 else 'normal'
        result.append(FinalLaunch(token,p.pair_address,p.dex_name,age,total,buys,sells,len(buyers),len(sellers),round(pressure,2),liq,vol,risk,level,anomaly,status,reasons+risk_notes))
    rank={'hot':3,'watch':2,'normal':1,'filter':0}
    return sorted(result,key=lambda x:(rank[x.status],x.anomaly_score,-x.risk_score),reverse=True)[:limit]
