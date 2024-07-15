CODE = """# https://vyper-by-example.org/verify-signature/
# @version ^0.3.9


# hash = getHash("Hello Vyper!")
# 0x5436c86f18e3d25a10e557ae125450118dd0a481ca22112b1977d55a676e4c91
@external
@pure
def getHash(_str: String[100]) -> bytes32:
    return keccak256(_str)


# getEthSignedHash(hash)
# 0x045b623a8e8fb7b4fcfbd1ae07e7326d55303d7de4085c69b346bd130c1936da
@external
@pure
def getEthSignedHash(_hash: bytes32) -> bytes32:
    return keccak256(
        concat(
            b'\x19Ethereum Signed Message:\n32',
            _hash
        )
    )


# account = your account
# hash = getHash("Hello Vyper!")
# signature = await ethereum.request({ method: "personal_sign", params: [account, hash]})
@external
@pure
def recoverSigner(ethSignedHash: bytes32, sig: Bytes[65]) -> address:
    r: uint256 = convert(slice(sig, 0, 32), uint256)
    s: uint256 = convert(slice(sig, 32, 32), uint256)
    v: uint256 = convert(slice(sig, 64, 1), uint256)
    return ecrecover(ethSignedHash, v, r, s)


@external
@pure
def verify(sig: Bytes[65], _str: String[100], _signer: address) -> bool:
    _hash: bytes32 = keccak256(_str)
    ethSignedHash: bytes32 = keccak256(
        concat(
            b'\x19Ethereum Signed Message:\n32',
            _hash
        )
    )
    r: uint256 = convert(slice(sig, 0, 32), uint256)
    s: uint256 = convert(slice(sig, 32, 32), uint256)
    v: uint256 = convert(slice(sig, 64, 1), uint256)
    signer: address = ecrecover(ethSignedHash, v, r, s)

    return _signer == signer
"""
ABI = [
    {
        "stateMutability": "pure",
        "type": "function",
        "name": "getHash",
        "inputs": [{"name": "_str", "type": "string"}],
        "outputs": [{"name": "", "type": "bytes32"}],
    },
    {
        "stateMutability": "pure",
        "type": "function",
        "name": "getEthSignedHash",
        "inputs": [{"name": "_hash", "type": "bytes32"}],
        "outputs": [{"name": "", "type": "bytes32"}],
    },
    {
        "stateMutability": "pure",
        "type": "function",
        "name": "recoverSigner",
        "inputs": [
            {"name": "ethSignedHash", "type": "bytes32"},
            {"name": "sig", "type": "bytes"},
        ],
        "outputs": [{"name": "", "type": "address"}],
    },
    {
        "stateMutability": "pure",
        "type": "function",
        "name": "verify",
        "inputs": [
            {"name": "sig", "type": "bytes"},
            {"name": "_str", "type": "string"},
            {"name": "_signer", "type": "address"},
        ],
        "outputs": [{"name": "", "type": "bool"}],
    },
]
BYTECODE = "0x61038d6100116100003961038d610000f35f3560e01c60026003821660011b61038501601e395f51565b635b6beeb98118610057576044361034176103815760043560040160648135116103815760208135018082604037505060405160602060e052602060e0f35b6397aba7f9811861037d57606436103417610381576024356004016041813511610381576020813501808260403750506040516020116103815760605161010052602060e05260e06020810151815160200360031b1c905060c05260405160401161038157608051610120526020610100526101006020810151815160200360031b1c905060e0526040516041116103815760a051610140526001610120526101206020810151815160200360031b1c9050610100525f6101a05260043561012052610100516101405260c0516101605260e0516101805260206101a0608061012060015afa506101a0516101c05260206101c0f361037d565b632f4ea5ea81186101d157602436103417610381575f601c6040527f19457468657265756d205369676e6564204d6573736167653a0a33320000000060605260408051602082018360a001815181525050808301925050506004358160a00152602081019050806080526080905080516020820120905060e052602060e0f35b631c1c6aea811861037d5760a436103417610381576004356004016041813511610381576020813501808260403750506024356004016064813511610381576020813501808260c03750506044358060a01c610381576101605260c05160e020610180525f601c6101c0527f19457468657265756d205369676e6564204d6573736167653a0a3332000000006101e0526101c080516020820183610220018151815250508083019250505061018051816102200152602081019050806102005261020090508051602082012090506101a052604051602011610381576060516102005260206101e0526101e06020810151815160200360031b1c90506101c05260405160401161038157608051610220526020610200526102006020810151815160200360031b1c90506101e0526040516041116103815760a051610240526001610220526102206020810151815160200360031b1c9050610200525f6102c0526101a0516102405261020051610260526101c051610280526101e0516102a05260206102c0608061024060015afa506102c05161022052610220516101605114610240526020610240f35b5f5ffd5b5f80fd037d00180151037d8419038d810800a16576797065728300030a0014"

from web3 import Web3, EthereumTesterProvider


w3 = Web3(EthereumTesterProvider())

# provide `constructor` args if appropriate:
deploy = w3.eth.contract(abi=ABI, bytecode=BYTECODE).constructor().transact()
contract_address = w3.eth.get_transaction_receipt(deploy)["contractAddress"]
contract = w3.eth.contract(address=contract_address, abi=ABI)

# result = contract.functions.exampleFunction().call()

fnx = contract.all_functions()
for fn in fnx:
    import pdb

    pdb.set_trace()  # noqa
    print(fn.fn_name)
