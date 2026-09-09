TRANSFER_TOPIC="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a3df523b3ef"
PAIR_CREATED_TOPIC="0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9"
SWAP_V2_TOPIC="0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
TOKEN0_SELECTOR="0x0dfe1681"
TOKEN1_SELECTOR="0xd21220a7"
def topic_address(topic_word: str)->str: return "0x"+topic_word[-40:]
def decode_transfer(log):
    t=log.get("topics",[])
    if len(t)<3 or t[0].lower()!=TRANSFER_TOPIC: return None
    return {"token_address":log["address"].lower(),"from_address":topic_address(t[1]).lower(),"to_address":topic_address(t[2]).lower(),"amount_raw":int(log.get("data","0x0"),16),"tx_hash":log["transactionHash"],"log_index":int(log["logIndex"],16),"block_number":int(log["blockNumber"],16)}
def decode_pair_created(log):
    t=log.get("topics",[]); data=log.get("data","0x")[2:]
    if len(t)<3 or t[0].lower()!=PAIR_CREATED_TOPIC or len(data)<64:return None
    return {"token0":topic_address(t[1]).lower(),"token1":topic_address(t[2]).lower(),"pair_address":topic_address("0x"+data[:64]).lower(),"block_number":int(log["blockNumber"],16)}
def decode_v2_swap(log):
    t=log.get("topics",[]); data=log.get("data","0x")[2:]
    if len(t)<2 or t[0].lower()!=SWAP_V2_TOPIC or len(data)<256:return None
    vals=[int(data[i:i+64],16) for i in range(0,256,64)]
    return {"pair_address":log["address"].lower(),"tx_hash":log["transactionHash"],"log_index":int(log["logIndex"],16),"sender":topic_address(t[1]).lower(),"amount0_in":vals[0],"amount1_in":vals[1],"amount0_out":vals[2],"amount1_out":vals[3],"block_number":int(log["blockNumber"],16)}
