"""
AP2 Payment MCP Server — Phase 4: The Governance Layer

PROTOCOL: AP2 (Agentic Payment Protocol) + ACF (Agentic Commerce Framework)
TRANSPORT: MCP stdio (FastMCP)

This server exposes the entire AP2 + ACF payment stack as MCP tools.
The Buyer Agent calls these tools instead of making HTTP calls directly,
keeping all payment logic isolated and auditable.

TOOLS:
  create_mandate   — human operator sets spending policy before run begins
  check_mandate    — AP2 policy check before any payment
  approve_payment  — ACF human override: terminal prompt for BLOCK decisions
  execute_payment  — AP2 + MPP: execute across fiat (Stripe) + USDC rails
  get_mandate      — inspect current mandate state

FLOW:
  1. Human calls create_mandate once (sets approved sellers, limits, tiers)
  2. Agent calls check_mandate before every payment
  3a. AUTO decision → agent calls execute_payment directly
  3b. NOTIFY decision → agent calls execute_payment, server logs notification
  3c. BLOCK decision → agent calls approve_payment to get human input
       If approved → human_approved=True → agent calls execute_payment
       If denied   → payment stops
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp.server.fastmcp import FastMCP

from src.payment_server.mandate import create_mandate, get_mandate, check_mandate, record_spend
from src.payment_server.rails import execute_payment as _execute_payment

mcp = FastMCP("SupplyMind Payment Server")

# In-memory store for human approval decisions keyed by mandate_id + seller_id
_approvals: dict[str, bool] = {}


@mcp.tool()
def tool_create_mandate(
    buyer_id:         str,
    approved_sellers: str,
    max_per_tx_usd:   float,
    max_total_usd:    float,
) -> dict:
    """
    AP2: Create a spending Mandate for the Buyer Agent.
    Call this once before the procurement run begins.

    approved_sellers: comma-separated seller IDs, or '*' for any seller.
    Returns the mandate dict including mandate_id for all subsequent calls.
    """
    sellers = [s.strip() for s in approved_sellers.split(",")]
    return create_mandate(buyer_id, sellers, max_per_tx_usd, max_total_usd)


@mcp.tool()
def tool_get_mandate(mandate_id: str) -> dict:
    """AP2: Retrieve current mandate state including spent total and tx count."""
    return get_mandate(mandate_id)


@mcp.tool()
def tool_check_mandate(
    mandate_id: str,
    amount_usd: float,
    seller_id:  str,
) -> dict:
    """
    AP2 + ACF: Check whether a payment is allowed under the Mandate.

    Returns:
      decision: 'approve' | 'notify' | 'block'
      reason:   explanation
      remaining_limit: USD remaining in mandate budget

    Call this before every payment. Never skip this check.
    """
    return check_mandate(mandate_id, amount_usd, seller_id)


@mcp.tool()
def tool_approve_payment(
    mandate_id: str,
    amount_usd: float,
    seller_id:  str,
    reason:     str,
) -> dict:
    """
    ACF BLOCK override: prompt the human operator for approval at the terminal.

    When check_mandate returns decision='block', call this tool.
    It prints the payment details to the terminal and waits for Y/N input.

    Returns:
      {"approved": True}  — human said yes, proceed to execute_payment
      {"approved": False} — human said no, stop
    """
    print(f"\n{'='*60}")
    print(f"  ACF BLOCK — Human Approval Required")
    print(f"{'='*60}")
    print(f"  Mandate   : {mandate_id}")
    print(f"  Seller    : {seller_id}")
    print(f"  Amount    : ${amount_usd:.2f}")
    print(f"  Reason    : {reason}")
    print(f"{'='*60}")

    mandate = get_mandate(mandate_id)
    if "error" not in mandate:
        print(f"  Spent so far : ${mandate['spent_total_usd']:.2f} / ${mandate['max_total_usd']:.2f}")

    try:
        answer = input("  Approve this payment? [Y/n]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = "n"

    approved = answer in ("", "y", "yes")
    key = f"{mandate_id}:{seller_id}:{amount_usd}"
    _approvals[key] = approved

    print(f"  Decision: {'APPROVED' if approved else 'DENIED'}\n")
    return {"approved": approved, "mandate_id": mandate_id, "amount_usd": amount_usd}


@mcp.tool()
def tool_execute_payment(
    mandate_id:     str,
    amount_usd:     float,
    seller_id:      str,
    wallet_address: str,
    acf_decision:   str,
    description:    str = "",
) -> dict:
    """
    AP2 + MPP: Execute payment across fiat (Stripe Test) and USDC (simulated) rails.

    Only call this after check_mandate returned 'approve' or 'notify',
    OR after approve_payment returned approved=True for a 'block' decision.

    acf_decision: the decision string returned by check_mandate ('approve'|'notify'|'block')

    On success: records the spend against the mandate and returns both rail results.
    """
    result = _execute_payment(
        acf_decision=acf_decision,
        amount_usd=amount_usd,
        seller_id=seller_id,
        wallet_address=wallet_address,
        mandate_id=mandate_id,
        description=description,
    )

    if result.get("status") == "executed":
        record_spend(mandate_id, amount_usd)

    return result


if __name__ == "__main__":
    mcp.run()
