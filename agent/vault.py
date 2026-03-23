# agent/vault.py
"""Interface to the YieldVault smart contract."""

from web3 import Web3
from eth_account import Account
from config import RPC_URL, YIELD_VAULT_ADDRESS, WSTETH_ADDRESS, AGENT_PRIVATE_KEY

# Minimal ABI — only what the agent needs
VAULT_ABI = [
    {
        "name": "availableYield",
        "type": "function",
        "inputs": [],
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view"
    },
    {
        "name": "availableYieldInStETH",
        "type": "function",
        "inputs": [],
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view"
    },
    {
        "name": "vaultState",
        "type": "function",
        "inputs": [],
        "outputs": [
            {"name": "totalBalance", "type": "uint256"},
            {"name": "principal", "type": "uint256"},
            {"name": "yieldAvailable", "type": "uint256"},
            {"name": "dailyRemaining", "type": "uint256"}
        ],
        "stateMutability": "view"
    },
    {
        "name": "withdrawYield",
        "type": "function",
        "inputs": [
            {"name": "recipient", "type": "address"},
            {"name": "wstETHAmount", "type": "uint256"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
]

WSTETH_ABI = [
    {
        "name": "balanceOf",
        "type": "function",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view"
    },
    {
        "name": "transfer",
        "type": "function",
        "inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "outputs": [{"type": "bool"}],
        "stateMutability": "nonpayable"
    },
]

# Initialize Web3 and contracts
w3 = Web3(Web3.HTTPProvider(RPC_URL))
vault = w3.eth.contract(address=Web3.to_checksum_address(YIELD_VAULT_ADDRESS), abi=VAULT_ABI)
agent_account = Account.from_key(AGENT_PRIVATE_KEY)


def get_vault_state() -> dict:
    """Read current state from YieldVault contract."""
    try:
        state = vault.functions.vaultState().call()
        return {
            "total_balance_eth": w3.from_wei(state[0], "ether"),
            "principal_eth": w3.from_wei(state[1], "ether"),
            "yield_available_eth": w3.from_wei(state[2], "ether"),
            "daily_remaining_eth": w3.from_wei(state[3], "ether"),
            "yield_available_wei": state[2],
        }
    except Exception as e:
        raise Exception(f"Failed to get vault state: {str(e)}")


def withdraw_yield_to_agent(amount_wei: int) -> str:
    """
    Withdraw yield from vault to agent wallet.
    Returns transaction hash.
    """
    try:
        nonce = w3.eth.get_transaction_count(agent_account.address)
        gas_price = w3.eth.gas_price

        tx = vault.functions.withdrawYield(
            agent_account.address,
            amount_wei
        ).build_transaction({
            "from": agent_account.address,
            "nonce": nonce,
            "gasPrice": gas_price,
            "gas": 200000,
            "chainId": w3.eth.chain_id,
        })

        signed = agent_account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        if receipt.status != 1:
            raise Exception(f"Transaction failed: {tx_hash.hex()}")

        return tx_hash.hex()
    except Exception as e:
        raise Exception(f"Failed to withdraw yield: {str(e)}")
