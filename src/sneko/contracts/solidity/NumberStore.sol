// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract NumberStore {
  uint256 public number;

  constructor(uint256 _number) {
    number = _number;
  }

  function setNumber(uint256 _number) public {
    number = _number;
  }

  function getNumber() public view returns (uint256) {
    return number;
  }
}
