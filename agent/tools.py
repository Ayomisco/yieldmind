# agent/tools.py
"""All LangChain tools the YieldMind agent can call."""

import json
import requests
from langchain.tools import tool
from web3 import Web3

import vault as vault_module
from config import (
    UNISWAP_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    VENICE_API_KEY, YIELD_THRESHOLD_ETH
)


@tool
def check_vault_state() -> str:
    """
    Check the current state of the YieldVault contract.
    Returns: principal locked, yield available, daily remaining cap.
    Always call this first before any other action.
    """
    try:
        state = vault_module.get_vault_state()
        return json.dumps({
            "principal_locked_eth": float(state["principal_eth"]),
            "yield_available_eth": float(state["yield_available_eth"]),
            "daily_remaining_eth": float(state["daily_remaining_eth"]),
            "can_act": float(state["yield_available_eth"]) > YIELD_THRESHOLD_ETH,
            "message": f"Vault healthy. {float(state['yield_available_eth']):.6f} ETH yield available."
        })
    except Exception as e:
        return json.dumps({"error": str(e), "can_act": False})


@tool
def withdraw_yield_for_compute(amount_eth: float) -> str:
    """
    Withdraw a small amount of accrued yield to pay for this agent's compute costs.
    Only call this when yield is available and compute needs to be funded.
    Amount must be small (< 0.005 ETH) and within daily cap.
    This is the self-funding mechanism - principal is never touched.
    """
    try:
        amount_wei = Web3.to_wei(amount_eth, "ether")
        state = vault_module.get_vault_state()

        if amount_wei > state["yield_available_wei"]:
            return json.dumps({"error": "Insufficient yield. Cannot touch principal.", "success": False})

        tx_hash = vault_module.withdraw_yield_to_agent(amount_wei)
        return json.dumps({
            "success": True,
            "tx_hash": tx_hash,
            "amount_withdrawn_eth": amount_eth,
            "message": f"Self-funding: withdrew {amount_eth} ETH yield for compute. TxHash: {tx_hash}"
        })
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


@tool
def get_uniswap_quote(token_in: str, token_out: str, amount_eth: float, chain_id: int = 84532) -> str:
    """
    Get a swap quote from Uniswap API.
    Use this to check if a token swap is favorable before executing.
    chain_id 84532 = Base Sepolia (testnet), 8453 = Base Mainnet.
    """
    try:
        amount_wei = str(int(Web3.to_wei(amount_eth, "ether")))
        url = "https://api.uniswap.org/v2/quote"
        params = {
            "tokenInAddress": token_in,
            "tokenInChainId": chain_id,
            "tokenOutAddress": token_out,
            "tokenOutChainId": chain_id,
            "amount": amount_wei,
            "type": "EXACT_INPUT",
        }
        headers = {"x-api-key": UNISWAP_API_KEY}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        return json.dumps({
            "quote_received": True,
            "amount_in_eth": amount_eth,
            "amount_out": data.get("quote", {}).get("amount", "unknown"),
            "price_impact": data.get("quote", {}).get("priceImpact", "unknown"),
            "raw": data
        })
    except Exception as e:
        return json.dumps({"error": str(e), "quote_received": False})


@tool
def execute_uniswap_swap(token_in: str, token_out: str, amount_eth: float, max_slippage_percent: float = 0.5) -> str:
    """
    Execute a real token swap via Uniswap API on Base.
    ONLY call this after calling get_uniswap_quote and deciding the trade is good.
    Returns a real transaction ID on Base.
    """
    try:
        amount_wei = str(int(Web3.to_wei(amount_eth, "ether")))
        url = "https://api.uniswap.org/v2/swap"
        payload = {
            "tokenInAddress": token_in,
            "tokenInChainId": 84532,
            "tokenOutAddress": token_out,
            "tokenOutChainId": 84532,
            "amount": amount_wei,
            "type": "EXACT_INPUT",
            "slippageTolerance": str(max_slippage_percent),
            "recipient": vault_module.agent_account.address,
            "deadline": 1800,
        }
        headers = {
            "x-api-key": UNISWAP_API_KEY,
            "Content-Type": "application/json"
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        data = resp.json()

        if "txHash" in data:
            return json.dumps({
                "success": True,
                "tx_hash": data["txHash"],
                "amount_in_eth": amount_eth,
                "message": f"Swap executed. TxHash: {data['txHash']}"
            })
        else:
            return json.dumps({"success": False, "error": "No txHash in response", "raw": data})
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


@tool
def analyze_market_conditions() -> str:
    """
    Fetch basic market data to inform trading decisions.
    Returns ETH price, stETH APY estimate, and market conditions summary.
    """
    try:
        # DeFiLlama - free, no auth
        resp = requests.get("https://api.llama.fi/protocol/lido", timeout=10)
        lido_data = resp.json() if resp.status_code == 200 else {}

        # ETH price from CoinGecko (free tier)
        price_resp = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=ethereum,lido-staked-ether&vs_currencies=usd",
            timeout=10
        )
        prices = price_resp.json() if price_resp.status_code == 200 else {}

        eth_price = prices.get("ethereum", {}).get("usd", "unknown")
        steth_price = prices.get("lido-staked-ether", {}).get("usd", "unknown")
        lido_tvl = lido_data.get("tvl", [{}])[-1].get("totalLiquidityUSD", "unknown") if lido_data.get("tvl") else "unknown"

        return json.dumps({
            "eth_price_usd": eth_price,
            "steth_price_usd": steth_price,
            "lido_tvl_usd": lido_tvl,
            "conditions": "Fetched successfully",
            "recommendation": "Conditions look stable" if eth_price != "unknown" else "Unable to fetch full data"
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def send_telegram_report(message: str) -> str:
    """
    Send a status report or alert to the human operator via Telegram.
    Use this to report: yield earned, actions taken, errors, or daily summaries.
    Keep messages concise and informative.
    """
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"🌱 YieldMind\n\n{message}",
            "parse_mode": "HTML"
        }
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            return json.dumps({"sent": True, "message": "Telegram alert delivered"})
        else:
            return json.dumps({"sent": False, "error": resp.text})
    except Exception as e:
        return json.dumps({"sent": False, "error": str(e)})
