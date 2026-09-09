from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.config import settings
from app.models import Token, Signal, ContractScan
from app.services.bsc_final import final_bsc_launches
from app.services.contract_risk import scan_contract, risk_dict
from app.services.rpc import AsyncRPC
router=APIRouter(prefix='/api/v2')
async def auth(x_api_key: str|None=Header(default=None)):
    if x_api_key in settings.api_key_set:return x_api_key
    raise HTTPException(401,'Invalid API key')
@router.get('/bsc/launches')
async def launches(limit:int=Query(100,le=300),db:AsyncSession=Depends(get_db),_:str=Depends(auth)):
    return [x.dict() for x in await final_bsc_launches(db,limit)]
@router.get('/bsc/hot')
async def hot(limit:int=Query(50,le=100),db:AsyncSession=Depends(get_db),_:str=Depends(auth)):
    return [x.dict() for x in (await final_bsc_launches(db,limit*2)) if x.status=='hot'][:limit]
@router.get('/bsc/overview')
async def overview(db:AsyncSession=Depends(get_db),_:str=Depends(auth)):
    rows=await final_bsc_launches(db,200)
    return {'chain_id':56,'focus':'new_token_anomaly','tracked_pairs':len(rows),'hot':sum(x.status=='hot' for x in rows),'watch':sum(x.status=='watch' for x in rows),'filtered':sum(x.status=='filter' for x in rows),'avg_anomaly':round(sum(x.anomaly_score for x in rows)/len(rows),2) if rows else 0}
@router.get('/bsc/risk/{token_address}')
async def risk(token_address:str,db:AsyncSession=Depends(get_db),_:str=Depends(auth)):
    row=(await db.execute(select(ContractScan).where(ContractScan.chain_id==56,ContractScan.token_address==token_address.lower()))).scalar_one_or_none()
    if not row: raise HTTPException(404,'Risk scan not available yet')
    return {'chain_id':56,'token':row.token_address,'owner':row.owner_address,'risk_score':row.risk_score,'risk_level':row.risk_level,'mint_capable_hint':row.mint_capable_hint,'pause_capable_hint':row.pause_capable_hint,'blacklist_hint':row.blacklist_hint,'proxy_hint':row.proxy_hint,'delegatecall_hint':row.delegatecall_hint,'selfdestruct_hint':row.selfdestruct_hint}
