# pragma version ~=0.4.0


number: uint256

@deploy
def __init__(number: uint256):
    self.number = number

@external
def set_number(number: uint256):
    self.number = number

@external
@view
def get_number() -> uint256:
    return self.number
