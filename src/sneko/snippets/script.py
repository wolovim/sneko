from web3 import Web3, EthereumTesterProvider


w3 = Web3(EthereumTesterProvider())

contract_factory = w3.eth.contract(abi=ABI, bytecode=BYTECODE)

import pdb; pdb.set_trace() # noqa

# provide `constructor` args if appropriate:
tx_hash = contract_factory.constructor().transact()
contract_address = w3.eth.get_transaction_receipt(tx_hash)["contractAddress"]
contract = w3.eth.contract(address=contract_address, abi=ABI)

# result = contract.functions.exampleFunction().call()
