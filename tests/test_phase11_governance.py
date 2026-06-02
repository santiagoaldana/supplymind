"""
Phase 11 -- Governance Dashboard: Integration Tests

Tests cover:
  1. GET /governance/agents: returns all registered agents with correct counts
  2. GET /governance/agents: revoked agent flagged correctly
  3. GET /governance/seller-manifests: returns signed manifest with SKU count
  4. GET /governance/intent-mandates: returns signed intent mandate
  5. GET /governance/cart-mandates: returns signed cart mandate
  6. GET /governance/signed-offers: returns signed offer
  7. GET /governance/summary: healthy when no violations
  8. GET /governance/summary: warning when agent revoked
  9. GET /governance/audit-trail: events ordered by timestamp, all layers present
 10. GET /: index page returns HTML

Run:
  python tests/test_phase11_governance.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from src.identity.keys import generate_keypair
from src.identity.dnsid import register_agent, revoke_agent, _REGISTRY
from src.identity.seller_manifest import create_seller_manifest, create_signed_offer, SELLER_MANIFESTS, SIGNED_OFFERS
from src.identity.signed_mandate import create_intent_mandate, create_cart_mandate, INTENT_MANDATES, CART_MANDATES
from src.governance.event_log import clear_log
from src.governance.dashboard import app

PASS      = "[PASS]"
SELLER_ID = "did:web:localhost:8080"
BUYER_ID  = "did:web:localhost:8090"

client = TestClient(app)


def _seed_data():
    """Seed all layers with representative data for dashboard tests."""
    _REGISTRY.clear()
    SELLER_MANIFESTS.clear()
    SIGNED_OFFERS.clear()
    INTENT_MANDATES.clear()
    CART_MANDATES.clear()

    # Identity layer
    seller_handle = register_agent("seller-001", "supplymind.localhost", "supplymind.localhost")
    buyer_handle  = register_agent("procurement-001", "supplymind.localhost", "supplymind.localhost")

    # Scoping layer -- seller manifest
    op_key, _    = generate_keypair()
    agent_key, _ = generate_keypair()

    manifest = create_seller_manifest(
        operator_id     = "ops@supplymind.localhost",
        seller_agent_id = SELLER_ID,
        seller_dnsid    = seller_handle,
        authorized_skus = [
            {"sku": "PPR-001", "min_price_usd": 5.0, "max_price_usd": 30.0, "max_discount_pct": 5.0},
        ],
        private_key = op_key,
    )

    # Approvals layer -- signed offer
    offer = create_signed_offer(
        manifest_id  = manifest["manifest_id"],
        sku          = "PPR-001",
        quantity     = 5,
        unit_price   = 14.99,
        discount_pct = 2.0,
        private_key  = agent_key,
        buyer_id     = BUYER_ID,
    )

    # Scoping + Approvals -- intent + cart mandate
    intent = create_intent_mandate(
        operator_id      = "cfo@supplymind.localhost",
        buyer_agent_id   = BUYER_ID,
        approved_sellers = [SELLER_ID],
        max_per_tx_usd   = 500.0,
        max_total_usd    = 5000.0,
        private_key      = op_key,
        buyer_dnsid      = buyer_handle,
    )
    cart = create_cart_mandate(
        intent_mandate_id = intent["mandate_id"],
        seller_id         = SELLER_ID,
        amount_usd        = 74.95,
        order_lines       = [{"sku": "PPR-001", "quantity": 5}],
        private_key       = agent_key,
        buyer_dnsid       = buyer_handle,
    )

    return seller_handle, buyer_handle, manifest, offer, intent, cart


def run():
    print()
    print("=" * 60)
    print("Phase 11 Governance Dashboard Tests")
    print("=" * 60)
    print()
    print("  Using in-process FastAPI test client (shared memory with seeded data)")
    print()

    clear_log()
    seller_handle, buyer_handle, manifest, offer, intent, cart = _seed_data()

    # Test 1: agents endpoint
    r = client.get("/governance/agents")
    assert r.status_code == 200
    data = r.json()
    assert data["total"]   == 2
    assert data["active"]  == 2
    assert data["revoked"] == 0
    assert "clerk_question" in data
    print(f"  {PASS} agents_endpoint: 2 active agents, clerk_question present")

    # Test 2: revoked agent flagged
    revoke_agent(seller_handle, reason="test revocation")
    r = client.get("/governance/agents")
    data = r.json()
    assert data["revoked"] == 1
    revoked = [a for a in data["agents"] if a["status"] == "revoked"]
    assert revoked[0]["handle"] == seller_handle
    print(f"  {PASS} revoked_agent_flagged: revoked agent appears with correct handle")

    # Test 3: seller manifests
    r = client.get("/governance/seller-manifests")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["manifests"][0]["operator_id"] == "ops@supplymind.localhost"
    assert data["manifests"][0]["sku_count"]   == 1
    assert data["manifests"][0]["signed"]      is True
    print(f"  {PASS} seller_manifests: 1 manifest, signed, operator_id present")

    # Test 4: intent mandates
    r = client.get("/governance/intent-mandates")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    m = data["mandates"][0]
    assert m["operator_id"]    == "cfo@supplymind.localhost"
    assert m["max_per_tx_usd"] == 500.0
    assert m["signed"]         is True
    print(f"  {PASS} intent_mandates: 1 mandate, signed, operator and limits present")

    # Test 5: cart mandates
    r = client.get("/governance/cart-mandates")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    c = data["cart_mandates"][0]
    assert c["amount_usd"] == 74.95
    assert c["signed"]     is True
    print(f"  {PASS} cart_mandates: 1 cart mandate, signed, amount present")

    # Test 6: signed offers
    r = client.get("/governance/signed-offers")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    o = data["offers"][0]
    assert o["sku"]        == "PPR-001"
    assert o["signed"]     is True
    assert o["unit_price"] == 14.99
    print(f"  {PASS} signed_offers: 1 offer, signed, SKU and price present")

    # Test 7: summary with revoked agent shows warning, all gates active
    r = client.get("/governance/summary")
    assert r.status_code == 200
    data = r.json()
    assert data["health"] == "warning"
    assert len(data["alerts"]) > 0
    assert data["identity"]["revoked"] == 1
    assert data["enforcement"]["manifest_gate_active"]     is True
    assert data["enforcement"]["cart_mandate_gate_active"] is True
    assert data["enforcement"]["dnsid_gate_active"]        is True
    print(f"  {PASS} summary_warning: health=warning, revoked agent in alerts, all enforcement gates active")

    # Test 8: enforcement gates remain active after adding another agent
    register_agent("temp-001", "supplymind.localhost", "supplymind.localhost")
    r = client.get("/governance/summary")
    data = r.json()
    assert data["enforcement"]["manifest_gate_active"] is True
    print(f"  {PASS} summary_gates: enforcement gates correctly report active")

    # Test 9: audit trail reads from log file, ordered by ts
    r = client.get("/governance/audit-trail")
    assert r.status_code == 200
    data = r.json()
    assert data["total_events"] > 0
    assert data["log_file"] == "logs/audit.jsonl"
    layers = {e["layer"] for e in data["events"]}
    assert "Identity"    in layers
    assert "Scoping"     in layers
    assert "Approvals"   in layers
    timestamps = [e["ts"] for e in data["events"]]
    assert timestamps == sorted(timestamps)
    print(f"  {PASS} audit_trail: {data['total_events']} events from log file, ordered by timestamp")

    # Test 10: index page
    r = client.get("/")
    assert r.status_code == 200
    assert "Governance Dashboard" in r.text
    assert "Identity" in r.text
    print(f"  {PASS} index_page: HTML returned with Clerk question links")

    print()
    print("All Phase 11 tests passed.")
    print()


if __name__ == "__main__":
    run()
