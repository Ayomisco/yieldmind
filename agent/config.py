# agent/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Synthesis
SYNTHESIS_API_KEY = os.environ.get("SYNTHESIS_API_KEY", "")
SYNTHESIS_PARTICIPANT_ID = os.environ.get("SYNTHESIS_PARTICIPANT_ID", "")
SYNTHESIS_TEAM_ID = os.environ.get("SYNTHESIS_TEAM_ID", "")

# Blockchain
BASE_SEPOLIA_RPC = os.environ.get("BASE_SEPOLIA_RPC_URL", "https://sepolia.base.org")
BASE_MAINNET_RPC = os.environ.get("BASE_MAINNET_RPC_URL", "https://mainnet.base.org")
AGENT_PRIVATE_KEY = os.environ.get("AGENT_PRIVATE_KEY", "")

# APIs
VENICE_API_KEY = os.environ.get("VENICE_API_KEY", "")
UNISWAP_API_KEY = os.environ.get("UNISWAP_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Contracts
YIELD_VAULT_ADDRESS = os.environ.get("YIELD_VAULT_ADDRESS", "0x44cF9A17e5D976f3D63a497068E2eC2D0a36B9Ae")
WSTETH_ADDRESS = os.environ.get("MOCK_WSTETH_ADDRESS", "0x91F0106205D87EAB2e7541bb2a09d5b933f94937")

# Agent settings
LOOP_INTERVAL_MINUTES = 10
YIELD_THRESHOLD_ETH = 0.001   # Only act when yield > this
USE_TESTNET = os.environ.get("USE_TESTNET", "true").lower() == "true"

RPC_URL = BASE_SEPOLIA_RPC if USE_TESTNET else BASE_MAINNET_RPC
