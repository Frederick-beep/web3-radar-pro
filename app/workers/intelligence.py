import asyncio,json
from redis.asyncio import Redis
from app.core.config import settings
from app.database import SessionLocal
from app.services.intelligence import process_transfer
async def main():
    r=Redis.from_url(settings.redis_url,decode_responses=True); group="intelligence"; stream="radar:logs"
    try: await r.xgroup_create(stream,group,id="0",mkstream=True)
    except Exception: pass
    while True:
        rows=await r.xreadgroup(group,"worker-1",{stream:">"},count=100,block=5000)
        if not rows: continue
        async with SessionLocal() as db:
            for _,messages in rows:
                for mid,data in messages:
                    try:
                        if data.get("type")=="transfer": await process_transfer(db,int(data["chain_id"]),__import__("app.services.erc20",fromlist=["decode_transfer"]).decode_transfer(json.loads(data["payload"])))
                        await r.xack(stream,group,mid)
                    except Exception as e: print("worker error",e)
if __name__=="__main__": asyncio.run(main())
