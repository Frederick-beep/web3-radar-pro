import asyncio, aiohttp

class AsyncRPC:
    def __init__(self, url: str, timeout: int = 20):
        self.url = url; self.timeout = timeout; self._id = 0
    async def call(self, method: str, params: list):
        if not self.url: raise RuntimeError("RPC URL is not configured")
        self._id += 1; payload = {"jsonrpc":"2.0","id":self._id,"method":method,"params":params}
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        last = None
        for attempt in range(3):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as s:
                    async with s.post(self.url, json=payload) as r:
                        r.raise_for_status(); data = await r.json()
                        if "error" in data: raise RuntimeError(data["error"])
                        return data["result"]
            except Exception as e:
                last = e
                if attempt < 2: await asyncio.sleep(2 ** attempt)
        raise last
    async def block_number(self): return int(await self.call("eth_blockNumber", []), 16)
    async def logs(self, from_block: int, to_block: int, topics=None, address=None):
        f={"fromBlock":hex(from_block),"toBlock":hex(to_block)}
        if topics: f["topics"]=topics
        if address: f["address"]=address
        return await self.call("eth_getLogs", [f])
    async def call_contract(self, address: str, data: str):
        return await self.call("eth_call", [{"to":address,"data":data},"latest"])
