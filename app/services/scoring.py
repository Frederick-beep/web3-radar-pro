def clamp(v): return max(0, min(100, int(v)))
def wallet_score(transfer_count, unique_tokens, inbound, outbound, whale_events):
    activity=min(25, transfer_count*2); diversity=min(20, unique_tokens*2)
    balance=20 if inbound and outbound else 8 if (inbound or outbound) else 0
    whales=min(25, whale_events*8); maturity=min(10, transfer_count//5)
    return clamp(activity+diversity+balance+whales+maturity)
def token_score(transfer_count, unique_wallets, whale_events, smart_wallets, liquidity_usd=0, volume_usd=0):
    return clamp(min(25, transfer_count//5)+min(25, unique_wallets//5)+min(20, whale_events*5)+min(20, smart_wallets*8)+min(5, liquidity_usd/100000)+min(5, volume_usd/100000))
def alpha_score(smart_wallets, whale_events, transfer_count, unique_wallets, volume_usd=0, liquidity_usd=0):
    return clamp(min(30,smart_wallets*6)+min(25,whale_events*5)+min(20,unique_wallets/10)+min(15,transfer_count/20)+min(5,volume_usd/100000)+min(5,liquidity_usd/100000)+min(10,smart_wallets*2))
