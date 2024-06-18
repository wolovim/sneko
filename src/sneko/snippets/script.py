from web3 import Web3, EthereumTesterProvider


w3 = Web3(EthereumTesterProvider())

# provide `constructor` args if appropriate:
deploy = w3.eth.contract(abi=ABI, bytecode=BYTECODE).constructor().transact()
contract_address = w3.eth.get_transaction_receipt(deploy)["contractAddress"]
contract = w3.eth.contract(address=contract_address, abi=ABI)

# result = contract.functions.exampleFunction().call()
