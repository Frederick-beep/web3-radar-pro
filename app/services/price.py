import aiohttp

class PriceService:
    async def token(self, chain_id:int, address:str):
        # DexScreener uses chain slugs; this service is deliberately optional.
        slug={1:"ethereum",56:"bsc",8453:"base"}.get(chain_id)
        if not slug: return None
        url=f"https://api.dexscreener.com/latest/dex/tokens/{address}"
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as s:
                async with s.get(url) as r:
                    if r.status!=200:return None
                    data=await r.json(); pairs=data.get("pairs") or []
                    pairs=[p for p in pairs if p.get("chainId")==slug]
                    if not pairs:return None
                    p=max(pairs,key=lambda x:float((x.get("liquidity") or {}).get("usd") or 0))
                    return {"price_usd":float(p.get("priceUsd") or 0),"liquidity_usd":float((p.get("liquidity") or {}).get("usd") or 0),"volume_24h_usd":float((p.get("volume") or {}).get("h24") or 0),"dex":(p.get("dexId") or "")}
        except Exception:return None
