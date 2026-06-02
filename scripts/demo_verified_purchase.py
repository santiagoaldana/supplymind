"""
Demo: Verified Purchase with Full Credential Chain

Simulates a real-world agentic purchase where the buyer has:
  1. A registered DNSid handle (identity)
  2. A human-signed Intent Mandate (scoping + approvals)
  3. A signed Cart Mandate (per-transaction authorization)

Sends both a UCP purchase and an ACP purchase, each fully credentialed.
Then queries the governance dashboard to show the difference between
anonymous purchases (from the earlier demo) and verified ones.

Run with both servers already running:
  Terminal 1: python src/seller_agent/server.py
  Terminal 2: python src/governance/dashboard.py
  Terminal 3: python scripts/demo_verified_purchase.py
"""

import sys
import json
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.identity.keys import generate_keypair
from src.identity.dnsid import register_agent, _REGISTRY
from src.identity.signed_mandate import create_intent_mandate, create_cart_mandate

SELLER_URL     = "http://localhost:8080"
GOVERNANCE_URL = "http://localhost:8085"
SELLER_ID      = "did:web:localhost:8080"
BUYER_ID       = "did:web:localhost:8090"
BUYER_DNSID    = "dnsid://supplymind.localhost/agents/procurement-001"


def separator(title: str):
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def show(label: str, data: dict, keys: list[str]):
    print(f"\n  {label}:")
    for k in keys:
        v = data.get(k) or data.get("result", {}).get(k)
        print(f"    {k}: {v}")


def main():
    separator("Step 1: Register buyer agent in DNSid")
    # The buyer's DNSid handle is already seeded by the server at startup.
    # We confirm it resolves correctly.
    r = httpx.get(f"{SELLER_URL}/governance/data/agents")
    agents = r.json()
    buyer_agent = next((a for a in agents if "procurement-001" in a["handle"]), None)
    if buyer_agent:
        print(f"  Buyer agent found in registry:")
        print(f"    handle: {buyer_agent['handle']}")
        print(f"    owner:  {buyer_agent['owner']}")
        print(f"    status: {buyer_agent['status']}")
    else:
        print("  Buyer agent not in registry -- registering now")
        register_agent("procurement-001", "supplymind.localhost", "supplymind.localhost")
        print(f"  Registered: {BUYER_DNSID}")

    separator("Step 2: Human operator creates signed Intent Mandate")
    # This simulates the CFO or procurement manager setting spending policy.
    # In production this is a LoginID biometric signing ceremony.
    operator_key, _ = generate_keypair()
    agent_key, _    = generate_keypair()

    intent = create_intent_mandate(
        operator_id      = "cfo@acme-corp.example",
        buyer_agent_id   = BUYER_ID,
        approved_sellers = [SELLER_ID],
        max_per_tx_usd   = 500.0,
        max_total_usd    = 2000.0,
        private_key      = operator_key,
        buyer_dnsid      = BUYER_DNSID,
    )
    print(f"  Intent Mandate created:")
    print(f"    mandate_id:    {intent['mandate_id']}")
    print(f"    operator_id:   {intent['operator_id']}")
    print(f"    max_per_tx:    ${intent['max_per_tx_usd']}")
    print(f"    max_total:     ${intent['max_total_usd']}")
    print(f"    signed:        {'proof' in intent}")

    separator("Step 3: Buyer agent creates signed Cart Mandate for UCP purchase")
    # This is the per-transaction authorization -- the agent signs off on this
    # specific order before sending it to the seller.
    cart_ucp = create_cart_mandate(
        intent_mandate_id = intent["mandate_id"],
        seller_id         = SELLER_ID,
        amount_usd        = 29.98,
        order_lines       = [{"sku": "PPR-001", "quantity": 2}],
        private_key       = agent_key,
        buyer_dnsid       = BUYER_DNSID,
    )
    cart_ucp_with_intent = {**cart_ucp, "intent_mandate": intent}
    print(f"  Cart Mandate created:")
    print(f"    cart_mandate_id: {cart_ucp['cart_mandate_id']}")
    print(f"    seller_id:       {cart_ucp['seller_id']}")
    print(f"    amount_usd:      ${cart_ucp['amount_usd']}")
    print(f"    signed:          {'proof' in cart_ucp}")

    separator("Step 4: Send verified UCP purchase")
    r = httpx.post(
        f"{SELLER_URL}/tasks/send",
        json={
            "buyer_id":        BUYER_ID,
            "order_lines":     [{"sku": "PPR-001", "quantity": 2}],
            "origin_zip":      "10001",
            "destination_zip": "90210",
            "service_level":   "standard",
            "cart_mandate":    cart_ucp_with_intent,
        },
        headers={"X-Agent-DNSid": BUYER_DNSID},
        timeout=10.0,
    )
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    task = r.json()
    print(f"  Purchase result:")
    show("  Task", task, ["status", "protocol_of_record"])
    result = task["result"]
    print(f"    products_subtotal:      ${result['products_subtotal']}")
    print(f"    buyer_dnsid_verified:   {result['buyer_dnsid_verified']}")
    print(f"    cart_mandate_verified:  {result['cart_mandate_verified']}")
    print(f"    operator_id:            {result['operator_id']}")

    separator("Step 5: Send verified ACP purchase")
    cart_acp = create_cart_mandate(
        intent_mandate_id = intent["mandate_id"],
        seller_id         = SELLER_ID,
        amount_usd        = 44.97,
        order_lines       = [{"sku": "PPR-001", "quantity": 3}],
        private_key       = agent_key,
        buyer_dnsid       = BUYER_DNSID,
    )
    cart_acp_with_intent = {**cart_acp, "intent_mandate": intent}

    r = httpx.post(
        f"{SELLER_URL}/acp/v1/checkout",
        json={
            "buyer_id": BUYER_ID,
            "items":    [{"product_id": "PPR-001", "quantity": 3}],
            "shipping": {"origin": "10001", "destination": "90210", "service": "standard"},
            "cart_mandate": cart_acp_with_intent,
        },
        headers={"X-Agent-DNSid": BUYER_DNSID},
        timeout=10.0,
    )
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    task = r.json()
    print(f"  Purchase result:")
    show("  Task", task, ["status", "protocol_of_record"])
    result = task["result"]
    print(f"    products_subtotal:      ${result['products_subtotal']}")
    print(f"    buyer_dnsid_verified:   {result['buyer_dnsid_verified']}")
    print(f"    cart_mandate_verified:  {result['cart_mandate_verified']}")
    print(f"    operator_id:            {result['operator_id']}")

    separator("Step 6: Governance dashboard -- protocol breakdown")
    r = httpx.get(f"{GOVERNANCE_URL}/governance/protocols", timeout=5.0)
    data = r.json()
    print(f"  Total completed transactions: {data['total_completed']}")
    print(f"  By protocol: {data['by_protocol']}")
    print()
    print("  Transaction detail:")
    for t in data["transactions"]:
        print(f"    [{t['protocol_of_record'].upper()}] "
              f"buyer={t['buyer_id']} "
              f"${t['products_subtotal']} "
              f"dnsid={t['buyer_dnsid_verified']} "
              f"mandate={t['cart_mandate_verified']}")

    separator("Step 7: Governance summary")
    r = httpx.get(f"{GOVERNANCE_URL}/governance/summary", timeout=5.0)
    data = r.json()
    print(f"  Health:       {data['health']}")
    print(f"  Alerts:       {data['alerts'] or 'none'}")
    print(f"  Agents:       {data['identity']['total_agents']} total, {data['identity']['revoked']} revoked")
    print(f"  Manifests:    {data['scoping']['seller_manifests']} seller manifests")
    print(f"  Transactions: {data['approvals']['total_transactions']} completed")
    print(f"  Enforcement gates: manifest={data['enforcement']['manifest_gate_active']} "
          f"dnsid={data['enforcement']['dnsid_gate_active']} "
          f"mandate={data['enforcement']['cart_mandate_gate_active']}")

    separator("Step 8: Audit trail (last 6 events)")
    r = httpx.get(f"{GOVERNANCE_URL}/governance/audit-trail?limit=6", timeout=5.0)
    data = r.json()
    print(f"  Total events in log: {data['total_events']}")
    print(f"  Log file: {data['log_file']}")
    print()
    for e in data["events"][-6:]:
        print(f"  [{e['layer']:12}] {e['event']:30} {e['entity'][:50]}")
        print(f"               operator={e['operator']}  detail={e['detail'][:60]}")

    print()
    print("=" * 60)
    print("  Demo complete.")
    print("  Compare the verified purchases (dnsid=True, mandate=True)")
    print("  with the anonymous ones (dnsid=False, mandate=False).")
    print("  The audit trail in logs/audit.jsonl has the full history.")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
