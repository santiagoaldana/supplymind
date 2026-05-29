"""
AP2 Mandate Engine — Phase 4: The Procurement Layer

PROTOCOL: AP2 (Agentic Payment Protocol)

An AP2 Mandate is a spending policy contract set by the human operator.
It defines:
  - Who the agent can pay (approved_sellers)
  - Maximum spend per transaction
  - Maximum total spend across all transactions
  - ACF tier thresholds (when to auto-pay, notify, or block)

Every payment attempt calls check_mandate() before any money moves.
The agent cannot exceed mandate limits — the payment server enforces them.

ACF TIERS (Agentic Commerce Framework — The Governance Layer):
  AUTO   : amount < $5    → pay immediately, no notification
  NOTIFY : $5 to $10      → pay + log human notification
  BLOCK  : over $10       → stop, require human approval

This is "Tiered Autonomy" — the human sets policy once,
the agent operates within it indefinitely.
"""

import uuid
from datetime import datetime, timezone

MANDATES: dict[str, dict] = {}

ACF_AUTO_UNDER   = 5.00
ACF_NOTIFY_UNDER = 10.00


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_mandate(
    buyer_id:         str,
    approved_sellers: list[str],
    max_per_tx_usd:   float,
    max_total_usd:    float,
) -> dict:
    """
    AP2: Create a new spending Mandate for a Buyer Agent.
    Called once by the human operator before the procurement run begins.
    Returns the mandate dict including its ID for all subsequent calls.
    """
    mandate_id = str(uuid.uuid4())
    mandate = {
        "mandate_id":       mandate_id,
        "buyer_id":         buyer_id,
        "approved_sellers": approved_sellers,
        "max_per_tx_usd":   max_per_tx_usd,
        "max_total_usd":    max_total_usd,
        "spent_total_usd":  0.0,
        "tx_count":         0,
        "tiers": {
            "auto_approve_under": ACF_AUTO_UNDER,
            "notify_under":       ACF_NOTIFY_UNDER,
        },
        "created_at": _now(),
        "active":     True,
    }
    MANDATES[mandate_id] = mandate
    return mandate


def get_mandate(mandate_id: str) -> dict:
    """AP2: Retrieve a Mandate by ID."""
    mandate = MANDATES.get(mandate_id)
    if not mandate:
        return {"error": f"Mandate {mandate_id} not found"}
    return mandate


def check_mandate(
    mandate_id: str,
    amount_usd: float,
    seller_id:  str,
) -> dict:
    """
    AP2 + ACF: Check whether a payment is permitted under the Mandate.

    Returns a decision:
      approve → pay immediately (ACF AUTO, under $5)
      notify  → pay + log notification (ACF NOTIFY, $5 to $10)
      block   → stop, require human approval (ACF BLOCK, over $10)

    Also enforces hard limits:
      - Seller must be in approved_sellers list
      - Amount must not exceed max_per_tx_usd
      - Running total must not exceed max_total_usd
    """
    mandate = MANDATES.get(mandate_id)
    if not mandate:
        return {"decision": "block", "reason": f"Mandate {mandate_id} not found"}
    if not mandate["active"]:
        return {"decision": "block", "reason": "Mandate is inactive"}
    if seller_id not in mandate["approved_sellers"] and "*" not in mandate["approved_sellers"]:
        return {"decision": "block", "reason": f"Seller {seller_id} not in approved list"}
    if amount_usd > mandate["max_per_tx_usd"]:
        return {
            "decision": "block",
            "reason":   f"Amount ${amount_usd:.2f} exceeds per-tx limit ${mandate['max_per_tx_usd']:.2f}",
        }
    if mandate["spent_total_usd"] + amount_usd > mandate["max_total_usd"]:
        return {
            "decision": "block",
            "reason":   (
                f"Would exceed total mandate limit ${mandate['max_total_usd']:.2f}. "
                f"Already spent: ${mandate['spent_total_usd']:.2f}"
            ),
        }

    tiers = mandate["tiers"]
    if amount_usd < tiers["auto_approve_under"]:
        decision = "approve"
        reason   = f"ACF AUTO: ${amount_usd:.2f} is under ${tiers['auto_approve_under']:.2f} threshold"
    elif amount_usd < tiers["notify_under"]:
        decision = "notify"
        reason   = (
            f"ACF NOTIFY: ${amount_usd:.2f} is between "
            f"${tiers['auto_approve_under']:.2f} and ${tiers['notify_under']:.2f}"
        )
    else:
        decision = "block"
        reason   = f"ACF BLOCK: ${amount_usd:.2f} exceeds ${tiers['notify_under']:.2f} notify threshold"

    return {
        "decision":        decision,
        "reason":          reason,
        "amount_usd":      amount_usd,
        "seller_id":       seller_id,
        "mandate_id":      mandate_id,
        "spent_so_far":    mandate["spent_total_usd"],
        "remaining_limit": round(mandate["max_total_usd"] - mandate["spent_total_usd"], 2),
    }


def record_spend(mandate_id: str, amount_usd: float) -> dict:
    """AP2: Record a completed payment against the Mandate's running total."""
    mandate = MANDATES.get(mandate_id)
    if not mandate:
        return {"error": f"Mandate {mandate_id} not found"}
    mandate["spent_total_usd"] = round(mandate["spent_total_usd"] + amount_usd, 2)
    mandate["tx_count"]        += 1
    return mandate
