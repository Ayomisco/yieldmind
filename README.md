# YieldMind — AI Agent That Earns Its Keep

> An autonomous AI agent whose entire operating budget comes from stETH staking yield. Principal stays locked forever. Agent spends only the interest. The first economically self-sustaining AI agent on Ethereum.

## The Problem

AI agents require continuous funding. You provide capital, you maintain a budget, you pay when it breaks. **YieldMind changes this.**

Instead of draining your wallet, YieldMind:
1. **Locks stETH principal** in a smart contract (structurally inaccessible)
2. **Earns yield** from Lido staking (~3.7% APY)
3. **Self-funds** its own compute using only that yield
4. **Never touches principal** — enforced at the contract level

## How It Works

```
Humans deposit wstETH (Principal locked forever)
                    ↓
           Lido earns ~3.7% APY
                    ↓
    Yield accrues above principal snapshot
                    ↓
     Agent withdraws tiny amounts ($0.001-0.01)
                    ↓
   Uses yield to pay for Venice LLM inference
                    ↓
        Agent thinks, executes, earns budget
                    ↓
           Repeat infinitely
```

## Architecture

### Smart Contracts (Solidity/Foundry)

**YieldVault.sol** — Core contract
- Holds wstETH principal locked forever
- Tracks principal snapshot immutably
- Only yields (balance - principal) available to agent
- Per-tx cap: 0.01 wstETH
- Daily cap: 0.05 wstETH
- Recipient whitelist (agent can only withdraw to approved addresses)

**MockWstETH.sol** — Test-only mock
- Simulates wstETH on Base Sepolia
- `simulateYield()` for testing

### Agent (Python/LangChain/LangGraph)

**config.py** — Environment setup
- Synthesis API credentials
- RPC endpoints (Base Sepolia/Mainnet)
- API keys (Venice, Uniswap, Telegram)
- Contract addresses

**vault.py** — Contract interface
- Web3 bindings to YieldVault
- `get_vault_state()` — Query principal, yield, caps
- `withdraw_yield_to_agent()` — On-chain withdrawal

**tools.py** — LangChain tools (6 total)
1. `check_vault_state` — Query vault health
2. `withdraw_yield_for_compute` — Self-fund inference
3. `get_uniswap_quote` — Check swap prices
4. `execute_uniswap_swap` — Execute trades
5. `analyze_market_conditions` — Fetch ETH/stETH prices
6. `send_telegram_report` — Notify operator

**agent.py** — ReAct loop
- LangGraph agent orchestration
- Venice LLM (private, no data retention)
- Runs every 10 minutes
- Checks yield → reasons → acts → reports

## Deployment Status

### ✅ Contracts (Live on Base Sepolia)
- **YieldVault**: `0x44cF9A17e5D976f3D63a497068E2eC2D0a36B9Ae`
- **MockWstETH**: `0x91F0106205D87EAB2e7541bb2a09d5b933f94937`
- **BaseScan**: [View Contract](https://sepolia.basescan.org/address/0x44cF9A17e5D976f3D63a497068E2eC2D0a36B9Ae)

### ✅ Agent (Deployed to Railway)
- Runs 24/7 as background worker
- Checks yield every 10 minutes
- Sends Telegram updates to operator
- Executes on-chain withdrawals when profitable

## Quick Start (Local Dev)

```bash
# 1. Clone and setup
git clone https://github.com/Ayomisco/yieldmind.git
cd yieldmind
cp .env.example .env

# 2. Fill in .env with:
# - SYNTHESIS_API_KEY
# - AGENT_PRIVATE_KEY / DEPLOYER_PRIVATE_KEY
# - VENICE_API_KEY
# - UNISWAP_API_KEY
# - TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID
# - RPC endpoints

# 3. Test contracts
cd contracts
forge build
forge test -vvv

# 4. Deploy (testnet only)
forge script script/Deploy.s.sol \
  --rpc-url https://sepolia.base.org \
  --broadcast

# 5. Run agent locally
cd ../agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python agent.py
```

## Tech Stack

- **Smart Contracts**: Solidity 0.8.24, Foundry, OpenZeppelin
- **Agent**: Python 3.14, LangChain, LangGraph
- **LLM**: Venice (private inference, no data retention)
- **Blockchain**: Base Sepolia (OP Stack L2)
- **DEX**: Uniswap V2 API
- **Notifications**: Telegram Bot API
- **Deployment**: Railway

## Key Features

✅ **Principal Lock** — Structurally enforced at contract level
✅ **Self-Funding** — Agent pays for own compute from yield
✅ **Private LLM** — Venice inference (GDPR-compliant, no data retention)
✅ **On-Chain Execution** — Real swaps, real withdrawals on Base
✅ **Autonomous** — Runs 24/7 without human intervention
✅ **Transparent** — All transactions visible on BaseScan
✅ **Scalable** — Multiple agents can share same vault

## Bounty Alignment

### Lido ($9.7k)
- ✅ YieldVault holds wstETH with `principalSnapshot`
- ✅ `availableYield()` returns only (balance - principal)
- ✅ `withdrawYield()` reverts if amount > availableYield
- ✅ Configurable: per-tx cap, daily cap, recipient whitelist
- ✅ Demo shows agent spending yield without touching principal

### Venice ($11.5k)
- ✅ All LLM inference via `api.venice.ai/api/v1`
- ✅ No other LLM used (no OpenAI, no Anthropic direct)
- ✅ Vault data in Venice context
- ✅ Leverages no-data-retention guarantee

### Base ($10k)
- ✅ YieldVault deployed on Base Sepolia
- ✅ Agent wallet on Base
- ✅ On-chain transactions (deposits, withdrawals)
- ✅ BaseScan integration

### Uniswap ($5k)
- ✅ Real Uniswap API integration
- ✅ Swap execution with actual TxID
- ✅ BaseScan proof of execution
- ✅ Open source repository

### Open Track ($28k)
- ✅ Novel yield-funded agent mechanism
- ✅ Working end-to-end demo
- ✅ True agent autonomy
- ✅ Economic sustainability proof

## Project Structure

```
yieldmind/
├── CLAUDE.md              # Build instructions
├── README.md              # This file
├── .env                   # Secrets (never commit)
├── .env.example           # Template
├── .gitignore
├── railway.json           # Railway config
├── contracts/
│   ├── src/
│   │   ├── YieldVault.sol
│   │   └── MockWstETH.sol
│   ├── script/
│   │   └── Deploy.s.sol
│   └── lib/openzeppelin-contracts/
├── agent/
│   ├── config.py
│   ├── vault.py
│   ├── tools.py
│   ├── agent.py
│   └── requirements.txt
└── frontend/ (optional)
```

---

**Built for The Synthesis Hackathon**
*YieldMind — The agent that earns its keep.*
