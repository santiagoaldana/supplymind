"""
AP2 Payment Rails — Phase 4: The Two-Rail Settlement Layer

PROTOCOL: AP2 (Agentic Payment Protocol) + MPP (Machine Payments Protocol)

Two payment rails run side by side. Every payment attempt executes both
so the demo shows fiat and USDC results in a single run.

FIAT RAIL (Stripe Test Mode):
  Creates a real Stripe PaymentIntent against the Stripe Test API.
  No real money moves — test mode is isolated from live mode.
  Stripe requires a payment_method at confirmation. In test mode
  we use the canonical test payment method ID "pm_card_visa"
  which Stripe accepts on any test PaymentIntent.

USDC RAIL (Simulated):
  No blockchain, no API calls, zero cost.
  Generates a deterministic fake tx_hash from the payment params.
  In a production AP2 system this call goes to the Circle API
  (POST /v1/payments) with a real wallet address as the destination.

ACF decision is enforced BEFORE either rail is called:
  AUTO   → execute immediately, no human input
  NOTIFY → execute + log notification (no blocking)
  BLOCK  → return blocked result, do not execute

Both rails return a uniform result envelope:
  {rail, status, amount_usd, reference, executed_at}
"""

import hashlib
import os
from datetime import datetime, timezone

import stripe
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_TEST_KEY")

from src.payment_server.circle_client import (
    is_configured as circle_is_configured,
    transfer_usdc,
    wait_for_confirmation,
)

CIRCLE_BUYER_WALLET_ID = os.getenv("CIRCLE_BUYER_WALLET_ID", "")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def execute_fiat_payment(
    amount_usd:     float,
    seller_id:      str,
    mandate_id:     str,
    description:    str = "",
) -> dict:
    """
    MPP Fiat Rail: create and confirm a Stripe PaymentIntent in test mode.

    Stripe amount is in cents (integer). We round to 2 decimal places
    then multiply by 100 to avoid floating-point drift.
    """
    amount_cents = int(round(amount_usd, 2) * 100)

    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="usd",
            payment_method="pm_card_visa",
            confirm=True,
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            metadata={
                "mandate_id": mandate_id,
                "seller_id":  seller_id,
                "protocol":   "AP2/MPP",
            },
            description=description or f"SupplyMind AP2 payment to {seller_id}",
        )
        return {
            "rail":              "fiat",
            "status":            "succeeded" if intent.status == "succeeded" else intent.status,
            "amount_usd":        amount_usd,
            "reference":         intent.id,
            "stripe_status":     intent.status,
            "executed_at":       _now(),
        }
    except stripe.StripeError as exc:
        return {
            "rail":        "fiat",
            "status":      "failed",
            "amount_usd":  amount_usd,
            "reference":   None,
            "error":       str(exc),
            "executed_at": _now(),
        }


def execute_usdc_payment(
    amount_usd:      float,
    wallet_address:  str,
    mandate_id:      str,
) -> dict:
    """
    MPP USDC Rail.

    If CIRCLE_API_KEY and CIRCLE_BUYER_WALLET_ID are set in .env, executes a
    real Circle Programmable Wallet transfer on Sepolia testnet. The returned
    tx_hash is a real Ethereum transaction hash -- verifiable at
    https://sepolia.etherscan.io/tx/{tx_hash}

    If Circle is not configured, falls back to the Phase 4 simulated hash so
    all existing tests continue to work without a Circle account.
    """
    if circle_is_configured() and CIRCLE_BUYER_WALLET_ID:
        try:
            idempotency_key = f"{mandate_id}:{wallet_address}:{round(amount_usd, 2)}"
            tx = transfer_usdc(
                from_wallet_id=CIRCLE_BUYER_WALLET_ID,
                to_address=wallet_address,
                amount_usdc=amount_usd,
                idempotency_key=idempotency_key,
            )
            tx_id = tx.get("id", "")
            if tx_id:
                tx = wait_for_confirmation(tx_id)

            tx_hash  = tx.get("txHash", "")
            state    = tx.get("state", "UNKNOWN")
            explorer = f"https://sepolia.etherscan.io/tx/{tx_hash}" if tx_hash else ""

            return {
                "rail":            "usdc",
                "status":          "confirmed" if state == "COMPLETE" else state.lower(),
                "amount_usd":      amount_usd,
                "reference":       tx_hash,
                "wallet_address":  wallet_address,
                "circle_tx_id":    tx_id,
                "blockchain":      "ETH-SEPOLIA",
                "explorer_url":    explorer,
                "executed_at":     _now(),
            }
        except Exception as exc:
            return {
                "rail":           "usdc",
                "status":         "failed",
                "amount_usd":     amount_usd,
                "reference":      None,
                "wallet_address": wallet_address,
                "error":          str(exc),
                "executed_at":    _now(),
            }

    # Simulated fallback (no Circle credentials)
    raw = f"{mandate_id}:{wallet_address}:{amount_usd}:{_now()}"
    tx_hash = "0x" + hashlib.sha256(raw.encode()).hexdigest()

    return {
        "rail":           "usdc",
        "status":         "simulated",
        "amount_usd":     amount_usd,
        "reference":      tx_hash,
        "wallet_address": wallet_address,
        "note":           "Set CIRCLE_API_KEY + CIRCLE_BUYER_WALLET_ID in .env for real settlement",
        "executed_at":    _now(),
    }


def execute_payment(
    acf_decision:   str,
    amount_usd:     float,
    seller_id:      str,
    wallet_address: str,
    mandate_id:     str,
    description:    str = "",
) -> dict:
    """
    AP2 + ACF: Execute payment across both rails based on the ACF decision.

    approve → execute both rails immediately
    notify  → execute both rails + attach notification flag
    block   → do not execute, return blocked result

    Returns:
      {
        "acf_decision": ...,
        "fiat":         {...},   # only present if executed
        "usdc":         {...},   # only present if executed
        "notification": ...,     # only present if notify
      }
    """
    if acf_decision == "block":
        return {
            "acf_decision": "block",
            "status":       "blocked",
            "amount_usd":   amount_usd,
            "reason":       "Payment blocked by ACF policy. Human approval required.",
        }

    fiat = execute_fiat_payment(amount_usd, seller_id, mandate_id, description)
    usdc = execute_usdc_payment(amount_usd, wallet_address, mandate_id)

    result = {
        "acf_decision": acf_decision,
        "status":       "executed",
        "amount_usd":   amount_usd,
        "fiat":         fiat,
        "usdc":         usdc,
    }

    if acf_decision == "notify":
        result["notification"] = (
            f"HUMAN NOTIFICATION: ${amount_usd:.2f} payment to {seller_id} "
            f"executed under ACF NOTIFY tier. Stripe ref: {fiat.get('reference', 'N/A')}"
        )

    return result
