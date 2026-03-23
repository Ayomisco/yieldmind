// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title MockWstETH
 * @notice Test-only mock that simulates wstETH yield accrual.
 *         Call simulateYield() to increase balance without new deposits.
 */
contract MockWstETH is ERC20, Ownable {
    uint256 private _extraBalance; // simulates rebasing yield

    constructor() ERC20("Mock wstETH", "mwstETH") Ownable(msg.sender) {}

    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }

    // Simulates yield accrual — balance increases without new tokens
    function simulateYield(address vault, uint256 yieldAmount) external onlyOwner {
        _mint(vault, yieldAmount);
    }

    function getStETHByWstETH(uint256 wstETHAmount) external pure returns (uint256) {
        return wstETHAmount * 11 / 10; // 1 wstETH ≈ 1.1 stETH (simplified)
    }

    function getWstETHByStETH(uint256 stETHAmount) external pure returns (uint256) {
        return stETHAmount * 10 / 11;
    }
}
