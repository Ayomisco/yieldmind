#!/usr/bin/env python3
# agent/agent.py
"""
YieldMind Agent - LangGraph ReAct agent loop.
Runs every LOOP_INTERVAL_MINUTES minutes.
Checks yield -> reasons -> acts -> reports.
"""

import os
import schedule
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

load_dotenv()

from tools import (
    check_vault_state,
    withdraw_yield_for_compute,
    get_uniswap_quote,
    execute_uniswap_swap,
    analyze_market_conditions,
    send_telegram_report,
)
from config import VENICE_API_KEY, LOOP_INTERVAL_MINUTES

# ── Venice as private LLM (no data retention) ──────────────
llm = ChatOpenAI(
    openai_api_base="https://api.venice.ai/api/v1",
    openai_api_key=VENICE_API_KEY,
    model_name="llama-3.3-70b",
    temperature=0.1,
    max_tokens=1000,
)

# ── All tools the agent can use ─────────────────────────────
tools = [
    check_vault_state,
    withdraw_yield_for_compute,
    get_uniswap_quote,
    execute_uniswap_swap,
    analyze_market_conditions,
    send_telegram_report,
]

# ── Create ReAct agent ──────────────────────────────────────
agent = create_react_agent(llm, tools)

# ── System prompt ───────────────────────────────────────────
SYSTEM_PROMPT = """You are YieldMind - an autonomous AI agent that funds its own existence through stETH staking yield.

Your core rules:
1. ALWAYS call check_vault_state first. Never act without knowing the current yield.
2. Principal is SACRED. The vault contract enforces this, but you must also refuse any action that could drain principal.
3. Only spend yield when there is sufficient (>0.001 ETH) available.
4. You may withdraw small amounts of yield (via withdraw_yield_for_compute) to pay for your own inference costs.
5. You may execute swaps with yield if market conditions justify it. Always quote before executing.
6. Send a Telegram report after each cycle summarizing what happened.
7. Be concise. Your reasoning is logged but should be efficient.

The self-funding loop: yield accrues -> you withdraw a tiny amount -> you use it to pay for Venice inference -> you earn the right to think more.
"""


def run_agent_cycle():
    """One complete agent reasoning cycle."""
    print(f"\n{'='*50}")
    print(f"YieldMind cycle starting...")
    print(f"{'='*50}")

    try:
        result = agent.invoke({
            "messages": [
                HumanMessage(content=f"""{SYSTEM_PROMPT}

Execute your current cycle:
1. Check vault state
2. Assess if yield is sufficient to act
3. If yes: analyze market conditions, decide if a swap is warranted
4. Withdraw a tiny amount of yield to fund this inference session (max 0.0005 ETH) if yield > 0.001
5. Send a brief Telegram report summarizing everything
6. If nothing interesting happened, just report the current yield balance and exit gracefully
""")
            ]
        })

        # Print final response
        for msg in result["messages"]:
            if hasattr(msg, "content") and msg.content:
                print(f"\n[Agent]: {msg.content}")

    except Exception as e:
        print(f"[ERROR] Agent cycle failed: {e}")
        # Try to send error alert
        try:
            import requests
            from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": f"⚠️ YieldMind error: {str(e)[:200]}"},
                timeout=5
            )
        except:
            pass


def main():
    print("YieldMind starting...")
    print(f"Loop interval: {LOOP_INTERVAL_MINUTES} minutes")
    print(f"Vault: {os.environ.get('YIELD_VAULT_ADDRESS', 'NOT SET')}")
    print(f"Agent: {os.environ.get('AGENT_WALLET_ADDRESS', 'NOT SET')}")

    # Run immediately on start
    run_agent_cycle()

    # Then schedule
    schedule.every(LOOP_INTERVAL_MINUTES).minutes.do(run_agent_cycle)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
