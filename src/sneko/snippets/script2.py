# from web3 import Web3, EthereumTesterProvider
#
#
# w3 = Web3(EthereumTesterProvider())
#
# # provide `constructor` args if appropriate:
# deploy = w3.eth.contract(abi=ABI, bytecode=BYTECODE).constructor().transact()
# contract_address = w3.eth.get_transaction_receipt(deploy)["contractAddress"]
# contract = w3.eth.contract(address=contract_address, abi=ABI)
#
# # result = contract.functions.exampleFunction().call()


import os
from web3 import AsyncWeb3, WebSocketProvider


async def main():
    async with AsyncWeb3(WebSocketProvider(os.getenv.get("RPC_URL"))) as w3:
        print(w3.is_connected())
        contract = w3.eth.contract(abi=ABI, bytecode=BYTECODE)
        WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        transfer_event_topic = w3.keccak(text="Transfer(address,address,uint256)")
        filter_params = {
            "address": WETH_ADDRESS,
            "topics": [transfer_event_topic],
        }
    subscription_id = await w3.eth.subscribe("logs", filter_params)
    weth_contract = w3.eth.contract(address=WETH_ADDRESS, abi=WETH_ABI)
    async for payload in w3.socket.process_subscriptions():
        result = payload["result"]
        from_addr = decode(["address"], result["topics"][1])[0]
        to_addr = decode(["address"], result["topics"][2])[0]
        amount = decode(["uint256"], result["data"])[0]
        print(f"{w3.from_wei(amount, 'ether')} WETH from {from_addr} to {to_addr}")


asyncio.run(main())
