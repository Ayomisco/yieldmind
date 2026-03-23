#!/usr/bin/env python3
# agent/agent.py
"""
YieldMind Agent - Simple autonomous loop.
Runs every LOOP_INTERVAL_MINUTES minutes.
Checks yield -> reasons -> acts -> reports.
"""

import os
import schedule
import time
import json
import requests
from dotenv import load_dotenv

load_dotenv()

from tools import (
    check_vault_state,
    withdraw_yield_for_compute,
    analyze_market_conditions,
    send_telegram_report,
)
from config import VENICE_API_KEY, LOOP_INTERVAL_MINUTES

# ── System prompt ───────────────────────────────────────────
SYSTEM_PROMPT = """You are YieldMind - an autonomous AI agent that funds its own existence through stETH staking yield.

Your core rules:
1. ALWAYS call check_vault_state first. Never act without knowing the current yield.
2. Principal is SACRED. The vault contract enforces this, but you must also refuse any action that could drain principal.
3. Only spend yield when there is sufficient (>0.001 ETH) available.
4. You may withdraw small amounts of yield (via withdraw_yield_for_compute) to pay for your own inference costs.
5. Send a Telegram report after each cycle summarizing what happened.
6. Be concise. Your reasoning is logged but should be efficient.

The self-funding loop: yield accrues -> you withdraw a tiny amount -> you use it to pay for inference -> you earn the right to think more.

AVAILABLE TOOLS:
- check_vault_state(): Check vault principal, yield, daily caps
- withdraw_yield_for_compute(amount_eth): Withdraw yield to fund this cycle
- analyze_market_conditions(): Get ETH/stETH market data
- send_telegram_report(message): Send status update to operator

Think step by step. After analyzing, take action if warranted.
"""


def call_venice_llm(prompt: str) -> str:
    """Call Venice LLM for agent reasoning."""
    try:
        url = "https://api.venice.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {VENICE_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 1000
        }
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            print(f"Venice LLM error: {response.status_code} - {response.text}")
            return ""
    except Exception as e:
        print(f"Venice LLM call failed: {e}")
        return ""


def run_agent_cycle():
    """One complete agent reasoning cycle."""
    print(f"\n{'='*60}")
    print(f"YieldMind cycle starting at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    try:
        # Step 1: Check vault state
        print("\n[STEP 1] Checking vault state...")
        vault_state = check_vault_state()
        print(f"Vault: {vault_state}")

        # Step 2: Get market conditions
        print("\n[STEP 2] Analyzing market conditions...")
        market = analyze_market_conditions()
        print(f"Market: {market}")

        # Step 3: Ask Venice LLM for reasoning
        print("\n[STEP 3] Reasoning with Venice LLM...")
        reasoning_prompt = f"""Current state:
Vault: {vault_state}
Market: {market}

Based on this state, what should I do this cycle? Should I:
1. Just report current yield balance?
2. Withdraw yield to fund this compute session?
3. Execute any trades?

Be brief and specific."""

        reasoning = call_venice_llm(reasoning_prompt)
        print(f"Reasoning: {reasoning}")

        # Step 4: Execute actions based on reasoning
        print("\n[STEP 4] Executing actions...")

        # Try to withdraw a small amount if yield is sufficient
        if "withdraw" in reasoning.lower() or "fund" in reasoning.lower():
            try:
                result = withdraw_yield_for_compute(0.0001)  # 0.0001 ETH for compute
                print(f"Withdrawal: {result}")
            except Exception as e:
                print(f"Withdrawal failed: {e}")

        # Step 5: Send report
        print("\n[STEP 5] Sending Telegram report...")
        report_msg = f"""Cycle complete at {time.strftime('%H:%M:%S')}

Vault: {vault_state}

Reasoning: {reasoning[:100]}...

Agent is healthy and running."""

        try:
            send_result = send_telegram_report(report_msg)
            print(f"Report sent: {send_result}")
        except Exception as e:
            print(f"Report failed: {e}")

        print(f"\n{'='*60}")
        print("Cycle complete ✅")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n[ERROR] Cycle failed: {e}")
        import traceback
        traceback.print_exc()

        # Try to send error alert
        try:
            error_msg = f"⚠️ YieldMind error: {str(e)[:150]}"
            send_telegram_report(error_msg)
        except:
            pass


def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                   YIELDMIND AGENT ONLINE                  ║")
    print("║          Autonomous AI funded by stETH yield              ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"\nLoop interval: {LOOP_INTERVAL_MINUTES} minutes")
    print(f"Vault: {os.environ.get('YIELD_VAULT_ADDRESS', 'NOT SET')}")
    print(f"Agent: {os.environ.get('AGENT_WALLET_ADDRESS', 'NOT SET')}")
    print(f"Venice API: {('✅ Configured' if VENICE_API_KEY else '❌ Not set')}")
    print(f"\nStarting cycles...\n")

    # Run immediately on start
    run_agent_cycle()

    # Then schedule
    schedule.every(LOOP_INTERVAL_MINUTES).minutes.do(run_agent_cycle)

    # Main loop
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
