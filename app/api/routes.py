import hashlib
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Token,Wallet,Transfer,Signal,DexPool,DexSwap
from app.core.config import settings
from app.services.bsc_radar import bsc_launches
router=APIRouter(prefix="/api/v1")
async def auth(x_api_key: str|None=Header(default=None)):
    if x_api_key in settings.api_key_set:return x_api_key
    raise HTTPException(401,"Invalid API key")
@router.get("/health")
async def health(): return {"status":"ok","chains":[1,8453,56]}
@router.get("/tokens")
async def tokens(limit:int=Query(50,le=200),chain_id:int|None=None,db:AsyncSession=Depends(get_db),_:str=Depends(auth)):
    q=select(Token).order_by(desc(Token.updated_at)).limit(limit)
    if chain_id:q=q.where(Token.chain_id==chain_id)
    return [{"chain_id":x.chain_id,"address":x.address,"symbol":x.symbol,"price_usd":float(x.price_usd or 0),"liquidity_usd":float(x.liquidity_usd or 0),"volume_24h_usd":float(x.volume_24h_usd or 0)} for x in (await db.execute(q)).scalars()]
@router.get("/wallets")
async def wallets(limit:int=50,smart_only:bool=False,chain_id:int|None=None,db:AsyncSession=Depends(get_db),_:str=Depends(auth)):
    q=select(Wallet).order_by(desc(Wallet.smart_money_score)).limit(min(limit,200))
    if smart_only:q=q.where(Wallet.is_smart_money==True)
    if chain_id:q=q.where(Wallet.chain_id==chain_id)
    return [{"chain_id":x.chain_id,"address":x.address,"score":x.smart_money_score,"smart_money":x.is_smart_money,"transfers":x.transfer_count,"whales":x.whale_events} for x in (await db.execute(q)).scalars()]
@router.get("/transfers")
async def transfers(limit:int=50,chain_id:int|None=None,address:str|None=None,db:AsyncSession=Depends(get_db),_:str=Depends(auth)):
    q=select(Transfer).order_by(desc(Transfer.block_number)).limit(min(limit,200))
    if chain_id:q=q.where(Transfer.chain_id==chain_id)
    if address:q=q.where((Transfer.from_address==address.lower())|(Transfer.to_address==address.lower()))
    return [{"chain_id":x.chain_id,"block":x.block_number,"tx":x.tx_hash,"token":x.token_address,"from":x.from_address,"to":x.to_address,"amount_raw":str(x.amount_raw)} for x in (await db.execute(q)).scalars()]
@router.get("/signals")
async def signals(limit:int=50,min_score:int=0,signal_type:str|None=None,chain_id:int|None=None,db:AsyncSession=Depends(get_db),_:str=Depends(auth)):
    q=select(Signal).where(Signal.score>=min_score).order_by(desc(Signal.created_at)).limit(min(limit,200))
    if signal_type:q=q.where(Signal.signal_type==signal_type)
    if chain_id:q=q.where(Signal.chain_id==chain_id)
    return [{"id":x.id,"chain_id":x.chain_id,"type":x.signal_type,"token":x.token_address,"wallet":x.wallet_address,"score":x.score,"reason":x.reason,"created_at":x.created_at.isoformat()} for x in (await db.execute(q)).scalars()]
@router.get("/pools")
async def pools(limit:int=50,chain_id:int|None=None,db:AsyncSession=Depends(get_db),_:str=Depends(auth)):
    q=select(DexPool).order_by(desc(DexPool.created_block)).limit(min(limit,200))
    if chain_id:q=q.where(DexPool.chain_id==chain_id)
    return [{"chain_id":x.chain_id,"dex":x.dex_name,"pair":x.pair_address,"token0":x.token0,"token1":x.token1,"block":x.created_block} for x in (await db.execute(q)).scalars()]
@router.get("/swaps")
async def swaps(limit:int=50,chain_id:int|None=None,db:AsyncSession=Depends(get_db),_:str=Depends(auth)):
    q=select(DexSwap).order_by(desc(DexSwap.block_number)).limit(min(limit,200))
    if chain_id:q=q.where(DexSwap.chain_id==chain_id)
    return [{"chain_id":x.chain_id,"pair":x.pair_address,"tx":x.tx_hash,"sender":x.sender,"block":x.block_number,"amount0_in":str(x.amount0_in),"amount1_in":str(x.amount1_in),"amount0_out":str(x.amount0_out),"amount1_out":str(x.amount1_out)} for x in (await db.execute(q)).scalars()]

@router.get("/bsc/launches")
async def bsc_launches_api(limit:int=Query(100,le=200),db:AsyncSession=Depends(get_db),_:str=Depends(auth)):
    rows=await bsc_launches(db,limit)
    return [r.__dict__ for r in rows]

@router.get("/bsc/hot")
async def bsc_hot(limit:int=Query(50,le=100),db:AsyncSession=Depends(get_db),_:str=Depends(auth)):
    rows=[r for r in await bsc_launches(db,limit*2) if r.status=="hot"]
    return [r.__dict__ for r in rows[:limit]]

@router.get("/me")
async def me(_:str=Depends(auth)): return {"plan":"free","api_access":True}

@router.get("/bsc/risk/{token_address}")
async def bsc_risk(token_address: str, db: AsyncSession = Depends(get_db), _: str = Depends(auth)):
    from app.models import ContractScan
    import json
    row=(await db.execute(select(ContractScan).where(ContractScan.chain_id==56, ContractScan.token_address==token_address.lower()))).scalar_one_or_none()
    if not row: raise HTTPException(404, "Risk scan not available yet")
    return {"chain_id":56,"token":row.token_address,"owner":row.owner_address,"mint_capable_hint":row.mint_capable_hint,"pause_capable_hint":row.pause_capable_hint,"blacklist_hint":row.blacklist_hint,"proxy_hint":row.proxy_hint,"delegatecall_hint":row.delegatecall_hint,"selfdestruct_hint":row.selfdestruct_hint,"risk_score":row.risk_score,"risk_level":row.risk_level,"notes":json.loads(row.notes_json or "[]"),"scanned_at":row.scanned_at.isoformat()}
