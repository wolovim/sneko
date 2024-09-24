// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import "@openzeppelin/contracts/access/Ownable.sol";


contract PopupFaucet is Ownable {
    mapping(bytes32 => uint256) private codeFunds;
    mapping(bytes32 => bool) private codeReserved;

    event Create(bytes32 hashedCode, uint256 amount, address sender);
    event Drip(bytes32 hashedCode, address recipient, uint256 amount);
    event TopUp(bytes32 hashedCode, uint256 amount, address sender);

    constructor(address initialOwner) Ownable(initialOwner) {}

    function _hashedEventCode(string calldata eventCode) private view returns (bytes32) {
        return keccak256(abi.encodePacked(eventCode));
    }

    function create(string calldata eventCode) external payable {
        require(msg.value > 0, "No Ether sent");
        require(codeReserved[_hashedEventCode(eventCode)] == false, "Event already exists");

        codeFunds[_hashedEventCode(eventCode)] += msg.value;
        codeReserved[_hashedEventCode(eventCode)] = true;

        emit Create(_hashedEventCode(eventCode), msg.value, msg.sender);
    }

    function drip(address recipient, string calldata eventCode) external {
        uint256 dripAmount = 0.0001 ether;

        require(address(this).balance >= dripAmount, "Insufficient contract balance");
        require(codeFunds[_hashedEventCode(eventCode)] >= dripAmount, "Insufficient event balance");

        codeFunds[_hashedEventCode(eventCode)] -= dripAmount;
        payable(recipient).transfer(dripAmount);

        emit Drip(_hashedEventCode(eventCode), recipient, dripAmount);
    }

    function topUp(string calldata eventCode) external payable {
        require(msg.value > 0, "No Ether sent");
        require(this.codeAvailable(eventCode) == false, "Event has to be created already");

        codeFunds[_hashedEventCode(eventCode)] += msg.value;

        emit TopUp(_hashedEventCode(eventCode), msg.value, msg.sender);
    }

    function codeAvailable(string calldata eventCode) external view returns (bool) {
        return !codeReserved[_hashedEventCode(eventCode)];
    }

    function codeFundsAvailable(string calldata eventCode) external view returns (uint256) {
        return codeFunds[_hashedEventCode(eventCode)];
    }

    function withdraw() onlyOwner external {
        payable(msg.sender).transfer(address(this).balance);
    }
}
