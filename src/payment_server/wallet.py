"""
Agent Wallet Layer -- Phase 13a (High-Fidelity Mock)

TWO RAILS:

  stripe_link (fiat):
    One-time virtual card per agent task. Address format: pm_test_<uuid>.
    Mirrors Stripe PaymentIntent + PaymentMethod response schemas.
    In 13b: swap mock address generation for real Stripe API call.

  coinbase_usdc (stablecoin):
    Non-custodial USDC wallet on Base. Address format: 0x<hex>.
    Mirrors Coinbase AgentKit wallet + transaction response schemas.
    In 13b: swap mock for real Coinbase CDP AgentKit API call.

KEY ARCHITECTURAL ADDITION vs prior phases:
  Payment now actually moves between wallets. The buyer wallet is debited,
  the seller wallet is credited, the mandate running total is updated, and
  the event is logged. Prior phases recorded wallet_address in line items
  but never executed the transfer.

LOGINID HOOK:
  provision_wallet() accepts operator_id -- the human who authorized wallet
  creation. In production this is the LoginID biometric ceremony: the wallet
  is only created after the human operator passes FIDO2 authentication.
  Financial regulators require KYC on wallet owners; LoginID provides it.

MOCK vs PRODUCTION (13b):
  - stripe_link: replace _mock_stripe_address() with Stripe API call to
    create a PaymentIntent and attach a PaymentMethod.
  - coinbase_usdc: replace _mock_coinbase_address() with Coinbase AgentKit
    wallet.create() call against Base Sepolia testnet.
  All function signatures and return schemas are identical in both cases.
"""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

from src.governance.event_log import log_event

WALLETS:  dict[str, dict]        = {}
PAYMENTS: dict[str, list[dict]]  = {}   # wallet_id -> list of payment records


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mock_stripe_address(wallet_id: str) -> str:
    """Mock Stripe PaymentMethod ID. Format matches real Stripe pm_test_* IDs."""
    short = wallet_id.replace("-", "")[:24]
    return f"pm_test_{short}"


def _mock_coinbase_address(owner_id: str) -> str:
    """Mock Ethereum-compatible wallet address. Format matches real Base addresses."""
    digest = hashlib.sha256(owner_id.encode()).hexdigest()
    return "0x" + digest[:40]


def _mock_payment_ref(rail: str, task_id: str) -> str:
    """
    Mock payment reference ID.
    Stripe format: pi_test_<...>  (PaymentIntent ID)
    Coinbase format: 0x<...>      (transaction hash)
    """
    short = task_id.replace("-", "")[:24]
    if rail == "fiat":
        return f"pi_test_{short}"
    return "0x" + hashlib.sha256(task_id.encode()).hexdigest()[:64]


def provision_wallet(
    owner_id:        str,
    wallet_type:     str,
    initial_balance: float,
    owner_dnsid:     Optional[str] = None,
    operator_id:     Optional[str] = None,
) -> dict:
    """
    Provision a new wallet for an agent.

    wallet_type: "stripe_link" | "coinbase_usdc"

    operator_id is the human who authorized wallet creation -- in production
    this is the LoginID biometric ceremony result. Financial regulators require
    KYC proof on wallet owners; this field is the audit hook for that proof.

    Returns the wallet dict. In 13b, this function makes a real API call to
    Stripe or Coinbase before storing the wallet.
    """
    wallet_id = str(uuid.uuid4())
    rail      = "fiat" if wallet_type == "stripe_link" else "usdc"
    currency  = "USD"  if wallet_type == "stripe_link" else "USDC"
    address   = (
        _mock_stripe_address(wallet_id)
        if wallet_type == "stripe_link"
        else _mock_coinbase_address(owner_id)
    )

    wallet = {
        "wallet_id":      wallet_id,
        "owner_id":       owner_id,
        "owner_dnsid":    owner_dnsid,
        "operator_id":    operator_id,
        "wallet_type":    wallet_type,
        "rail":           rail,
        "address":        address,
        "balance":        round(initial_balance, 2),
        "currency":       currency,
        "status":         "active",
        "tx_count":       0,
        "created_at":     _now(),
        "provisioned_by": operator_id or "system",
    }
    WALLETS[wallet_id] = wallet
    PAYMENTS[wallet_id] = []

    log_event(
        "Enforcement", "wallet_provisioned", owner_id,
        operator_id or "system",
        f"wallet_id={wallet_id} type={wallet_type} balance={initial_balance} {currency}",
    )
    return dict(wallet)


def get_wallet(wallet_id: str) -> dict:
    """Retrieve a wallet by ID. Returns error dict if not found."""
    w = WALLETS.get(wallet_id)
    if not w:
        return {"error": f"Wallet {wallet_id} not found"}
    return dict(w)


def get_wallets_by_owner(owner_id: str) -> list[dict]:
    """Return all wallets for a given owner_id (buyer or seller agent)."""
    return [dict(w) for w in WALLETS.values() if w["owner_id"] == owner_id]


def execute_payment(
    from_wallet_id: str,
    to_wallet_id:   str,
    amount:         float,
    task_id:        str,
    mandate_id:     Optional[str] = None,
) -> dict:
    """
    Execute a payment between two wallets.

    Enforcement order (matches Clerk's sequence):
      1. Both wallets must exist and be active
      2. Wallets must be on the same rail (fiat-to-fiat or usdc-to-usdc)
      3. Buyer balance must cover the amount
      4. If mandate_id provided: amount must not exceed mandate max_per_tx_usd
      5. Debit buyer, credit seller
      6. Update mandate running total via record_spend()
      7. Log the payment event

    Returns payment result dict mirroring Stripe/Coinbase transaction schemas.
    In 13b: step 5 becomes a real API call.
    """
    buyer  = WALLETS.get(from_wallet_id)
    seller = WALLETS.get(to_wallet_id)

    if not buyer:
        return {"status": "failed", "reason": f"Buyer wallet {from_wallet_id} not found"}
    if not seller:
        return {"status": "failed", "reason": f"Seller wallet {to_wallet_id} not found"}
    if buyer["status"] != "active":
        return {"status": "failed", "reason": f"Buyer wallet is {buyer['status']}"}
    if buyer["rail"] != seller["rail"]:
        return {"status": "failed", "reason": f"Rail mismatch: {buyer['rail']} vs {seller['rail']}"}

    amount = round(amount, 2)

    if buyer["balance"] < amount:
        return {
            "status":         "insufficient_funds",
            "reason":         f"Wallet balance {buyer['balance']} {buyer['currency']} < {amount}",
            "balance":        buyer["balance"],
            "currency":       buyer["currency"],
            "amount_requested": amount,
        }

    if mandate_id:
        from src.payment_server.mandate import MANDATES
        mandate = MANDATES.get(mandate_id)
        if mandate and amount > mandate["max_per_tx_usd"]:
            return {
                "status": "failed",
                "reason": f"Amount ${amount} exceeds mandate per-tx limit ${mandate['max_per_tx_usd']}",
            }

    buyer["balance"]   = round(buyer["balance"]  - amount, 2)
    seller["balance"]  = round(seller["balance"] + amount, 2)
    buyer["tx_count"]  += 1
    seller["tx_count"] += 1

    if buyer["balance"] == 0:
        buyer["status"] = "depleted"

    if mandate_id:
        from src.payment_server.mandate import record_spend
        record_spend(mandate_id, amount)

    payment_ref = _mock_payment_ref(buyer["rail"], task_id)
    settled_at  = _now()

    payment_record = {
        "payment_ref":   payment_ref,
        "rail":          buyer["rail"],
        "from_wallet":   from_wallet_id,
        "to_wallet":     to_wallet_id,
        "amount":        amount,
        "currency":      buyer["currency"],
        "status":        "succeeded",
        "task_id":       task_id,
        "mandate_id":    mandate_id,
        "settled_at":    settled_at,
    }

    PAYMENTS[from_wallet_id].append(payment_record)
    PAYMENTS[to_wallet_id].append(payment_record)

    log_event(
        "Enforcement", "payment_executed",
        buyer["owner_id"], seller["owner_id"],
        f"payment_ref={payment_ref} amount={amount} {buyer['currency']} rail={buyer['rail']} task={task_id}",
        data={"amount": amount, "rail": buyer["rail"], "payment_ref": payment_ref},
    )

    return payment_record


def get_payment_history(wallet_id: str) -> list[dict]:
    """Return all payment records for a wallet (sent and received)."""
    if wallet_id not in PAYMENTS:
        return []
    return list(PAYMENTS[wallet_id])


def list_wallets() -> list[dict]:
    """Return all wallets. Used by governance dashboard."""
    return [dict(w) for w in WALLETS.values()]
