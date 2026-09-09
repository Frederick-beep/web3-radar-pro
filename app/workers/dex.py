import asyncio,json
from redis.asyncio import Redis
from sqlalchemy import select
from app.database import SessionLocal
from app.models import DexPool,DexSwap
from app.services.erc20 import decode_pair_created,decode_v2_swap,SWAP_V2_TOPIC
from app.services.rpc import AsyncRPC
from app.core.config import settings
import os,yaml
with open("config/chains.yaml","r",encoding="utf-8") as f: CFG=yaml.safe_load(f)["chains"]
async def add_pair(db, chain_id, data, dex, factory):
    old=(await db.execute(select(DexPool).where(DexPool.chain_id==chain_id,DexPool.pair_address==data["pair_address"]))).scalar_one_or_none()
    if old:return
    db.add(DexPool(chain_id=chain_id,factory=factory,dex_name=dex,pair_address=data["pair_address"],token0=data["token0"],token1=data["token1"],created_block=data["block_number"]))
    await db.commit()
async def scan_swaps(db, redis):
    for c in CFG:
        url=os.getenv(c["env"],"")
        if not url:continue
        rpc=AsyncRPC(url,settings.rpc_timeout)
        pools=(await db.execute(select(DexPool).where(DexPool.chain_id==c["id"]).order_by(DexPool.created_block.desc()).limit(200))).scalars().all()
        if not pools:continue
        head=await rpc.block_number()-settings.confirmations
        for p in pools:
            start=max(0,head-20)
            logs=await rpc.logs(start,head,[SWAP_V2_TOPIC],p.pair_address)
            for log in logs:
                d=decode_v2_swap(log)
                if not d:continue
                exists=(await db.execute(select(DexSwap).where(DexSwap.chain_id==c["id"],DexSwap.tx_hash==d["tx_hash"],DexSwap.log_index==d["log_index"]))).scalar_one_or_none()
                if not exists:db.add(DexSwap(chain_id=c["id"],**d))
        await db.commit()
async def main():
    r=Redis.from_url(settings.redis_url,decode_responses=True); group="dex"; stream="radar:dex"
    try:await r.xgroup_create(stream,group,id="0",mkstream=True)
    except Exception:pass
    while True:
        async with SessionLocal() as db:
            rows=await r.xreadgroup(group,"dex-1",{stream:">"},count=50,block=2000)
            if rows:
                for _,msgs in rows:
                    for mid,data in msgs:
                        try:
                            if data.get("type")=="pair_created":
                                d=decode_pair_created(json.loads(data["payload"]))
                                if d: await add_pair(db,int(data["chain_id"]),d,data.get("dex","DEX"),data.get("factory",""))
                            await r.xack(stream,group,mid)
                        except Exception as e: print("dex worker error",e)
            await scan_swaps(db,r)
        await asyncio.sleep(10)
if __name__=="__main__":asyncio.run(main())
