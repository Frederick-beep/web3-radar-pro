import json
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from app.models import Token, Transfer, Wallet, WalletToken, Signal, DexSwap
from app.services.scoring import wallet_score, alpha_score
from app.services.alerts import send_telegram
from app.core.config import settings

async def upsert_wallet(db, chain_id, address, block, inbound, whale):
    if address == "0x"+"0"*40:return None
    w=(await db.execute(select(Wallet).where(Wallet.chain_id==chain_id,Wallet.address==address))).scalar_one_or_none()
    if not w:
        w=Wallet(chain_id=chain_id,address=address); db.add(w); await db.flush()
    w.transfer_count+=1; w.inbound_count+=1 if inbound else 0; w.outbound_count+=0 if inbound else 1; w.whale_events+=1 if whale else 0; w.last_activity_block=max(w.last_activity_block,block)
    w.unique_tokens=int((await db.execute(select(func.count()).select_from(WalletToken).where(WalletToken.chain_id==chain_id,WalletToken.wallet_address==address))).scalar_one())
    w.smart_money_score=wallet_score(w.transfer_count,w.unique_tokens,w.inbound_count,w.outbound_count,w.whale_events)
    w.is_smart_money=w.smart_money_score>=80
    return w

async def process_transfer(db, chain_id, d):
    exists=(await db.execute(select(Transfer).where(Transfer.chain_id==chain_id,Transfer.tx_hash==d["tx_hash"],Transfer.log_index==d["log_index"]))).scalar_one_or_none()
    if exists:return
    token=(await db.execute(select(Token).where(Token.chain_id==chain_id,Token.address==d["token_address"]))).scalar_one_or_none()
    if not token:
        token=Token(chain_id=chain_id,address=d["token_address"],first_seen_block=d["block_number"],last_seen_block=d["block_number"]);db.add(token)
    else: token.last_seen_block=max(token.last_seen_block,d["block_number"])
    db.add(Transfer(chain_id=chain_id,**d))
    for addr,inbound in ((d["to_address"],True),(d["from_address"],False)):
        wt=(await db.execute(select(WalletToken).where(WalletToken.chain_id==chain_id,WalletToken.wallet_address==addr,WalletToken.token_address==d["token_address"]))).scalar_one_or_none()
        if not wt: wt=WalletToken(chain_id=chain_id,wallet_address=addr,token_address=d["token_address"]);db.add(wt)
        wt.transfers+=1; wt.inbound_raw+=d["amount_raw"] if inbound else 0; wt.outbound_raw+=d["amount_raw"] if not inbound else 0
    whale=d["amount_raw"]>=10**18*10000
    await upsert_wallet(db,chain_id,d["to_address"],d["block_number"],True,whale)
    await upsert_wallet(db,chain_id,d["from_address"],d["block_number"],False,whale)
    if whale:
        sig=Signal(chain_id=chain_id,signal_type="WHALE_TRANSFER",token_address=d["token_address"],wallet_address=d["to_address"],score=75,reason="Large ERC-20 transfer detected",metadata_json=json.dumps(d));db.add(sig)
    await db.commit()
    if whale and 75>=settings.telegram_min_score: await send_telegram(f"🐋 Whale transfer\nChain: {chain_id}\nToken: {d['token_address']}\nScore: 75")

async def refresh_token_signals(db, chain_id, token_address):
    transfers=int((await db.execute(select(func.count()).select_from(Transfer).where(Transfer.chain_id==chain_id,Transfer.token_address==token_address))).scalar_one())
    unique_wallets=int((await db.execute(select(func.count(func.distinct(Transfer.to_address))).where(Transfer.chain_id==chain_id,Transfer.token_address==token_address))).scalar_one())
    whales=int((await db.execute(select(func.count()).select_from(Signal).where(Signal.chain_id==chain_id,Signal.token_address==token_address,Signal.signal_type=="WHALE_TRANSFER"))).scalar_one())
    smart=int((await db.execute(select(func.count()).select_from(Wallet).join(WalletToken, (Wallet.chain_id==WalletToken.chain_id)&(Wallet.address==WalletToken.wallet_address)).where(Wallet.chain_id==chain_id,WalletToken.token_address==token_address,Wallet.is_smart_money==True))).scalar_one())
    t=(await db.execute(select(Token).where(Token.chain_id==chain_id,Token.address==token_address))).scalar_one_or_none()
    if not t:return
    score=alpha_score(smart,whales,transfers,unique_wallets,float(t.volume_24h_usd or 0),float(t.liquidity_usd or 0))
    if score>=settings.signal_min_score:
        db.add(Signal(chain_id=chain_id,signal_type="ALPHA_TOKEN",token_address=token_address,score=score,reason=f"SmartMoney={smart}; whales={whales}; wallets={unique_wallets}; transfers={transfers}",metadata_json=json.dumps({"smart_wallets":smart,"whale_events":whales,"unique_wallets":unique_wallets})))
        await db.commit()
