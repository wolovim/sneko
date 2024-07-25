# pragma version ~=0.4.0

from ethereum.ercs import IERC20
from ethereum.ercs import IERC20Detailed
from snekmate.auth import ownable
from snekmate.tokens import erc20


initializes: ownable
initializes: erc20[ownable := ownable]
exports: (
    erc20.owner,
    erc20.IERC20,
    erc20.IERC20Detailed,
    erc20.mint,
    erc20.set_minter,
)

initialSupply: public(uint256)

@deploy
def __init__(name_: String[25], symbol_: String[5], decimals_: uint8, initial_supply_: uint256, name_eip712_: String[50], version_eip712_: String[20]):
    # The following line assigns the `owner` to the `msg.sender`.
    ownable.__init__()
    # e.g., erc20.__init__("Vyper", "VY", 18, "Vyper", "1")
    erc20.__init__(name_, symbol_, decimals_, name_eip712_, version_eip712_)

    # The following line premints an initial token
    # supply to the `msg.sender`, which takes the
    # underlying `decimals` value into account.
    erc20._mint(msg.sender, initial_supply_ * 10 ** convert(decimals_, uint256))

    # We assign the initial token supply required by
    # the Echidna external harness contract.
    self.initialSupply = erc20.totalSupply
