from __future__ import annotations
from dataclasses import dataclass, asdict
from app.services.rpc import AsyncRPC

OWNER_SELECTOR = "0x8da5cb5b"

@dataclass
class ContractRisk:
    address: str
    has_code: bool
    owner: str | None
    mint_capable_hint: bool
    pause_capable_hint: bool
    blacklist_hint: bool
    proxy_hint: bool
    delegatecall_hint: bool
    selfdestruct_hint: bool
    risk_score: int
    risk_level: str
    notes: list[str]

def _clamp(v: int) -> int:
    return max(0, min(100, v))

async def _call(rpc: AsyncRPC, address: str, selector: str) -> str | None:
    try:
        return await rpc.call_contract(address, selector)
    except Exception:
        return None

async def scan_contract(rpc: AsyncRPC, address: str) -> ContractRisk:
    address = address.lower()
    code = await rpc.call("eth_getCode", [address, "latest"])
    bytecode = (code or "0x")[2:].lower()
    owner_raw = await _call(rpc, address, OWNER_SELECTOR)
    owner = None
    if owner_raw and len(owner_raw) >= 66:
        candidate = "0x" + owner_raw[-40:]
        if int(candidate, 16) != 0:
            owner = candidate

    # Conservative selector/opcode heuristics. These are NOT proofs of a vulnerability.
    mint = any(s in bytecode for s in ("40c10f19", "a0712d68"))
    pause = any(s in bytecode for s in ("8456cb59", "3f4ba83a"))
    blacklist = any(s in bytecode for s in ("f9f92be4", "443c028e"))
    proxy = bytecode.startswith("363d3d373d3d3d363d73") or "5af43d82803e903d91602b57fd5bf3" in bytecode
    delegatecall = "f4" in bytecode
    selfdestruct = "ff" in bytecode

    score = 0; notes=[]
    if owner: score += 10; notes.append("non-zero owner() detected")
    if mint: score += 25; notes.append("mint-like selector hint")
    if pause: score += 10; notes.append("pause-like selector hint")
    if blacklist: score += 20; notes.append("blacklist-like selector hint")
    if proxy: score += 15; notes.append("proxy pattern hint")
    if delegatecall: score += 5; notes.append("delegatecall opcode present")
    if selfdestruct: score += 10; notes.append("selfdestruct opcode present")
    score=_clamp(score)
    level="high" if score>=60 else "medium" if score>=30 else "low"
    return ContractRisk(address, bool(bytecode), owner, mint, pause, blacklist, proxy, delegatecall, selfdestruct, score, level, notes)

def risk_dict(result: ContractRisk) -> dict:
    return asdict(result)
