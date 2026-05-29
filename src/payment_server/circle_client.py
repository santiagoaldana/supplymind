"""
Circle Programmable Wallets Client -- Phase 8

WHAT THIS IS:
  Circle is the company that issues USDC (the stablecoin). Their Programmable
  Wallets API lets you create wallets and move USDC between them entirely via
  code -- no browser extension, no MetaMask, no manual signing.

  This module is a thin wrapper around three Circle API calls:
    create_wallet()          -- provision a new wallet for a seller
    transfer_usdc()          -- send USDC from buyer wallet to seller wallet
    get_transaction_status() -- poll until the transfer is confirmed

HOW CIRCLE TESTNET WORKS:
  Circle testnet (sandbox) uses real blockchain infrastructure but fake money.
  Transactions appear on the Sepolia Ethereum testnet and are verifiable on
  a real blockchain explorer. Zero cost, zero risk.

  Steps to get started (free):
    1. Create account at developers.circle.com
    2. Switch to Sandbox mode (toggle in dashboard)
    3. Copy your API key into .env as CIRCLE_API_KEY
    4. Circle gives you a pre-funded testnet wallet automatically

WHAT CHANGES FROM PHASE 4:
  execute_usdc_payment() in rails.py currently generates a fake SHA-256 hash.
  Phase 8 replaces that with a real Circle API call. The tx_hash that comes
  back is a real Ethereum transaction hash -- paste it into
  https://sepolia.etherscan.io to see the actual on-chain transfer.

ENVIRONMENT VARIABLES REQUIRED:
  CIRCLE_API_KEY          -- from developers.circle.com (sandbox mode)
  CIRCLE_BUYER_WALLET_ID  -- the buyer's Circle wallet ID (from dashboard)
"""

import os
import time
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

load_dotenv()

CIRCLE_API_BASE = "https://api-sandbox.circle.com/v1/w3s"
CIRCLE_API_KEY  = os.getenv("CIRCLE_API_KEY", "")

BLOCKCHAIN    = "ETH-SEPOLIA"
TOKEN_ID_USDC = "USDC"

POLL_TIMEOUT_SECONDS  = 60
POLL_INTERVAL_SECONDS = 3


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {CIRCLE_API_KEY}",
        "Content-Type":  "application/json",
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_configured() -> bool:
    """Return True if the Circle API key is present in the environment."""
    return bool(CIRCLE_API_KEY)


def create_wallet(entity_name: str) -> dict:
    """
    Create a new Circle Programmable Wallet for a seller entity.

    Returns the wallet dict from Circle:
      {id, state, walletSetId, custodyType, address, blockchain}

    The 'address' field is the public Ethereum address -- this is what goes
    into the seller's KYA document as their settlement address.
    """
    with httpx.Client(timeout=15.0) as client:
        r = client.post(
            f"{CIRCLE_API_BASE}/wallets",
            headers=_headers(),
            json={
                "idempotencyKey": f"supplymind-{entity_name}-{int(time.time())}",
                "blockchains":    [BLOCKCHAIN],
                "metadata":       [{"name": entity_name, "refId": entity_name}],
            },
        )
        r.raise_for_status()
        data = r.json()
        return data.get("data", {}).get("wallets", [{}])[0]


def transfer_usdc(
    from_wallet_id:  str,
    to_address:      str,
    amount_usdc:     float,
    idempotency_key: str = "",
) -> dict:
    """
    Transfer USDC from buyer's Circle wallet to seller's wallet address.

    from_wallet_id  -- Circle wallet ID of the buyer (not the address, the ID)
    to_address      -- Ethereum address of the seller (from their KYA wallet field)
    amount_usdc     -- dollar amount (Circle accepts string with 6 decimal places)
    idempotency_key -- unique string to prevent duplicate transfers on retry

    Returns the Circle transaction object:
      {id, state, txHash, ...}

    'state' starts as 'INITIATED', progresses to 'COMPLETE' or 'FAILED'.
    Use wait_for_confirmation() to poll until settled.
    """
    key = idempotency_key or f"supplymind-{from_wallet_id}-{to_address}-{int(time.time())}"

    with httpx.Client(timeout=15.0) as client:
        r = client.post(
            f"{CIRCLE_API_BASE}/transactions/transfer",
            headers=_headers(),
            json={
                "idempotencyKey":     key,
                "walletId":           from_wallet_id,
                "tokenId":            TOKEN_ID_USDC,
                "destinationAddress": to_address,
                "amounts":            [f"{amount_usdc:.6f}"],
                "blockchain":         BLOCKCHAIN,
                "feeLevel":           "MEDIUM",
            },
        )
        r.raise_for_status()
        data = r.json()
        return data.get("data", {}).get("transaction", {})


def get_transaction_status(transaction_id: str) -> dict:
    """
    Fetch the current state of a Circle transaction.

    Returns the transaction dict with at minimum:
      {id, state, txHash, blockchain, amounts, ...}

    Possible states: INITIATED, PENDING_RISK_SCREENING, SENT, CONFIRMED, COMPLETE, FAILED
    """
    with httpx.Client(timeout=10.0) as client:
        r = client.get(
            f"{CIRCLE_API_BASE}/transactions/{transaction_id}",
            headers=_headers(),
        )
        r.raise_for_status()
        data = r.json()
        return data.get("data", {}).get("transaction", {})


def wait_for_confirmation(transaction_id: str) -> dict:
    """
    Poll Circle until the transaction reaches COMPLETE or FAILED.

    Returns the final transaction dict.
    Raises TimeoutError if the transaction does not settle within
    POLL_TIMEOUT_SECONDS.

    COMPLETE transactions have a txHash field -- a real Ethereum transaction
    hash verifiable at https://sepolia.etherscan.io/tx/{txHash}
    """
    deadline = time.time() + POLL_TIMEOUT_SECONDS
    while time.time() < deadline:
        tx = get_transaction_status(transaction_id)
        state = tx.get("state", "")
        if state in ("COMPLETE", "FAILED"):
            return tx
        time.sleep(POLL_INTERVAL_SECONDS)
    raise TimeoutError(
        f"Transaction {transaction_id} did not settle within {POLL_TIMEOUT_SECONDS}s"
    )
