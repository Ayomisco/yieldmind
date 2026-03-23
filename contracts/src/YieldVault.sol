// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

interface IWstETH is IERC20 {
    function getStETHByWstETH(uint256 _wstETHAmount) external view returns (uint256);
    function getWstETHByStETH(uint256 _stETHAmount) external view returns (uint256);
}

/**
 * @title YieldVault
 * @notice Holds wstETH principal locked forever.
 *         Only accrued yield (above principal snapshot) can be withdrawn by the agent.
 *         Principal is structurally inaccessible to the agent.
 */
contract YieldVault is Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // ── State ──────────────────────────────────────────────────
    IWstETH public immutable wstETH;

    address public agent;                    // Agent wallet — can only spend yield
    uint256 public principalSnapshot;        // wstETH deposited (locked forever)

    uint256 public maxPerTxWei;              // Max yield withdrawal per tx
    uint256 public dailyCapWei;              // Max yield withdrawal per day
    uint256 public dailyWithdrawn;           // Yield withdrawn today
    uint256 public lastResetDay;             // Day number of last reset

    mapping(address => bool) public recipientWhitelist;

    // ── Events ────────────────────────────────────────────────
    event Deposited(address indexed depositor, uint256 wstETHAmount);
    event YieldWithdrawn(address indexed recipient, uint256 wstETHAmount);
    event AgentUpdated(address indexed newAgent);
    event CapUpdated(uint256 maxPerTx, uint256 dailyCap);

    // ── Constructor ───────────────────────────────────────────
    constructor(
        address _wstETH,
        address _agent,
        uint256 _maxPerTxWei,
        uint256 _dailyCapWei
    ) Ownable(msg.sender) {
        wstETH = IWstETH(_wstETH);
        agent = _agent;
        maxPerTxWei = _maxPerTxWei;
        dailyCapWei = _dailyCapWei;
        lastResetDay = block.timestamp / 1 days;
    }

    // ── Modifiers ─────────────────────────────────────────────
    modifier onlyAgent() {
        require(msg.sender == agent, "Only agent");
        _;
    }

    // ── Core: Deposit principal ───────────────────────────────
    /**
     * @notice Deposit wstETH as principal. This amount is LOCKED FOREVER.
     *         Yield above this amount accrues and becomes spendable.
     */
    function deposit(uint256 wstETHAmount) external nonReentrant {
        require(wstETHAmount > 0, "Amount must be > 0");
        IERC20(address(wstETH)).safeTransferFrom(msg.sender, address(this), wstETHAmount);
        principalSnapshot += wstETHAmount;
        emit Deposited(msg.sender, wstETHAmount);
    }

    // ── Core: Query available yield ───────────────────────────
    /**
     * @notice Returns how much wstETH yield has accrued above principal.
     *         This is what the agent can spend. Principal is untouched.
     */
    function availableYield() public view returns (uint256) {
        uint256 currentBalance = wstETH.balanceOf(address(this));
        if (currentBalance <= principalSnapshot) return 0;
        return currentBalance - principalSnapshot;
    }

    /**
     * @notice Returns available yield denominated in stETH (for display).
     */
    function availableYieldInStETH() external view returns (uint256) {
        uint256 yieldWstETH = availableYield();
        if (yieldWstETH == 0) return 0;
        return wstETH.getStETHByWstETH(yieldWstETH);
    }

    // ── Core: Withdraw yield (agent only) ─────────────────────
    /**
     * @notice Agent withdraws yield to a whitelisted recipient.
     *         Cannot touch principal. Enforces per-tx cap and daily cap.
     */
    function withdrawYield(address recipient, uint256 wstETHAmount) external nonReentrant onlyAgent {
        require(recipientWhitelist[recipient], "Recipient not whitelisted");
        require(wstETHAmount > 0 && wstETHAmount <= maxPerTxWei, "Exceeds per-tx cap");

        // Reset daily counter if new day
        uint256 today = block.timestamp / 1 days;
        if (today > lastResetDay) {
            dailyWithdrawn = 0;
            lastResetDay = today;
        }

        require(dailyWithdrawn + wstETHAmount <= dailyCapWei, "Exceeds daily cap");

        uint256 yield = availableYield();
        require(wstETHAmount <= yield, "Insufficient yield - principal is locked");

        dailyWithdrawn += wstETHAmount;
        IERC20(address(wstETH)).safeTransfer(recipient, wstETHAmount);
        emit YieldWithdrawn(recipient, wstETHAmount);
    }

    // ── Admin: Configuration ──────────────────────────────────
    function setAgent(address _agent) external onlyOwner {
        agent = _agent;
        emit AgentUpdated(_agent);
    }

    function setCaps(uint256 _maxPerTxWei, uint256 _dailyCapWei) external onlyOwner {
        maxPerTxWei = _maxPerTxWei;
        dailyCapWei = _dailyCapWei;
        emit CapUpdated(_maxPerTxWei, _dailyCapWei);
    }

    function addRecipient(address recipient) external onlyOwner {
        recipientWhitelist[recipient] = true;
    }

    function removeRecipient(address recipient) external onlyOwner {
        recipientWhitelist[recipient] = false;
    }

    // ── View helpers ──────────────────────────────────────────
    function vaultState() external view returns (
        uint256 totalBalance,
        uint256 principal,
        uint256 yieldAvailable,
        uint256 dailyRemaining
    ) {
        totalBalance = wstETH.balanceOf(address(this));
        principal = principalSnapshot;
        yieldAvailable = availableYield();

        uint256 today = block.timestamp / 1 days;
        uint256 usedToday = (today > lastResetDay) ? 0 : dailyWithdrawn;
        dailyRemaining = dailyCapWei > usedToday ? dailyCapWei - usedToday : 0;
    }
}
