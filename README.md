# YieldMind

An autonomous AI agent that funds its own compute using stETH staking yield. Principal stays locked forever — agent spends only the interest. The first economically self-sustaining AI agent on Ethereum.

## Quick Start

```bash
# 1. Copy env template
cp .env.example .env

# 2. Fill in your secrets (RPC URLs, API keys, private keys)
# 3. Deploy contracts
cd contracts && forge build && forge script script/Deploy.s.sol --rpc-url https://sepolia.base.org --broadcast

# 4. Set up agent
cd ../agent && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 5. Run
python agent.py
```

## Architecture

- **Smart Contract (Solidity)**: YieldVault holds wstETH principal locked forever, only yield flows to agent
- **Agent (Python/LangGraph)**: ReAct loop that checks vault yield, executes swaps, funds its own compute
- **Inference (Venice)**: Private LLM for agent reasoning (no data retention)

## Key Files

- `contracts/src/YieldVault.sol` — Core vault logic
- `agent/agent.py` — Main agent loop
- `agent/tools.py` — All LangChain tools

## Bounties

- Lido: stETH yield vault with principal lock guarantee
- Venice: Private LLM inference with no data retention
- Base: Smart contracts deployed on Base Sepolia/Mainnet
- Uniswap: Real token swaps executed by agent
- Open Track: Novel yield-funded autonomous agent
