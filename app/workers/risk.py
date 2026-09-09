import asyncio, json, os
from sqlalchemy import select
from app.database import SessionLocal
from app.models import DexPool, ContractScan
from app.services.rpc import AsyncRPC
from app.services.contract_risk import scan_contract
from app.core.config import settings
import yaml
with open("config/chains.yaml", "r", encoding="utf-8") as f: CFG=yaml.safe_load(f)["chains"]
WBNB="0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
async def run():
    while True:
        c=next(x for x in CFG if x["id"]==56)
        url=os.getenv(c["env"],"")
        if url:
            rpc=AsyncRPC(url,settings.rpc_timeout)
            async with SessionLocal() as db:
                pools=(await db.execute(select(DexPool).where(DexPool.chain_id==56).order_by(DexPool.created_block.desc()).limit(100))).scalars().all()
                seen=set()
                for p in pools:
                    token=(p.token1 if p.token0.lower()==WBNB else p.token0).lower()
                    if token in seen: continue
                    seen.add(token)
                    try: r=await scan_contract(rpc,token)
                    except Exception as e: print("risk scan error",token,e); continue
                    row=(await db.execute(select(ContractScan).where(ContractScan.chain_id==56,ContractScan.token_address==token))).scalar_one_or_none()
                    values=dict(owner_address=r.owner,mint_capable_hint=r.mint_capable_hint,pause_capable_hint=r.pause_capable_hint,blacklist_hint=r.blacklist_hint,proxy_hint=r.proxy_hint,delegatecall_hint=r.delegatecall_hint,selfdestruct_hint=r.selfdestruct_hint,risk_score=r.risk_score,risk_level=r.risk_level,notes_json=json.dumps(r.notes))
                    if row:
                        for k,v in values.items(): setattr(row,k,v)
                    else: db.add(ContractScan(chain_id=56,token_address=token,**values))
                await db.commit()
        await asyncio.sleep(30)
if __name__=="__main__": asyncio.run(run())
