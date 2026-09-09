import os, yaml, json, asyncio
from redis.asyncio import Redis
from app.core.config import settings
from app.services.rpc import AsyncRPC
from app.services.erc20 import TRANSFER_TOPIC, PAIR_CREATED_TOPIC
with open("config/chains.yaml","r",encoding="utf-8") as f: CHAIN_CFG=yaml.safe_load(f)["chains"]
def rpc_for(c): return AsyncRPC(os.getenv(c["env"],""),settings.rpc_timeout)
async def collect_chain(c, redis):
    rpc=rpc_for(c); latest=await rpc.block_number()-settings.confirmations; cursor=max(0,latest-settings.log_batch_blocks)
    while True:
        head=await rpc.block_number()-settings.confirmations
        if head<=cursor:
            await asyncio.sleep(settings.poll_interval); continue
        to=min(head,cursor+settings.log_batch_blocks)
        logs=await rpc.logs(cursor+1,to,[TRANSFER_TOPIC])
        for log in logs: await redis.xadd("radar:logs",{"chain_id":c["id"],"type":"transfer","payload":json.dumps(log)},maxlen=200000,approximate=True)
        for fac in c.get("dex_factories",[]):
            plogs=await rpc.logs(cursor+1,to,[PAIR_CREATED_TOPIC],fac["address"])
            for log in plogs: await redis.xadd("radar:dex",{"chain_id":c["id"],"type":"pair_created","dex":fac["name"],"factory":fac["address"],"payload":json.dumps(log)},maxlen=100000,approximate=True)
        cursor=to
async def run_collector():
    redis=Redis.from_url(settings.redis_url,decode_responses=True)
    tasks=[collect_chain(c,redis) for c in CHAIN_CFG if os.getenv(c["env"],"")]
    if not tasks: raise RuntimeError("No RPC URLs configured")
    await asyncio.gather(*tasks)
