from app.services.erc20 import decode_transfer,TRANSFER_TOPIC
def test_decode():
    log={"address":"0x"+"1"*40,"topics":[TRANSFER_TOPIC,"0x"+"0"*24+"2"*40,"0x"+"0"*24+"3"*40],"data":"0x64","transactionHash":"0x"+"a"*64,"logIndex":"0x0","blockNumber":"0x10"}
    x=decode_transfer(log)
    assert x["amount_raw"]==100 and x["to_address"]=="0x"+"3"*40
