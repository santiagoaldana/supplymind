"""
Phase 12 -- Multi-Protocol Checkout: Tests

Tests cover:
  1. Protocol router: ACP payload normalized correctly
  2. Protocol router: UCP payload normalized correctly
  3. Server: ACP checkout returns 201, protocol_of_record=acp
  4. Server: ACP checkout with revoked DNSid returns 403
  5. Server: UCP /tasks/send still works, protocol_of_record=ucp
  6. Server: ACP and UCP both produce protocol_of_record in result
  7. Governance: /governance/protocols shows correct protocol breakdown
  8. Security: ACP endpoint applies DNSid gate (same as UCP)
  9. Security: ACP endpoint applies Cart Mandate gate (same as UCP)

Run:
  python tests/test_phase12_multi_protocol.py
"""

import sys
import copy
import time
import subprocess
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.seller_agent.protocol_router import normalize_acp, normalize_ucp_task
from src.identity.dnsid import _TEST_REVOKED_HANDLE
from src.identity.keys import generate_keypair
from src.identity.signed_mandate import create_intent_mandate, create_cart_mandate, INTENT_MANDATES, CART_MANDATES

PASS            = "[PASS]"
SELLER_BASE_URL = "http://localhost:8080"
SELLER_ID       = "did:web:localhost:8080"
BUYER_ID        = "did:web:localhost:8090"

ACP_PAYLOAD = {
    "buyer_id": BUYER_ID,
    "items": [{"product_id": "PPR-001", "quantity": 1}],
    "shipping": {"origin": "10001", "destination": "90210", "service": "standard"},
}

UCP_PAYLOAD = {
    "buyer_id":        BUYER_ID,
    "order_lines":     [{"sku": "PPR-001", "quantity": 1}],
    "origin_zip":      "10001",
    "destination_zip": "90210",
    "service_level":   "standard",
}


# ── Unit tests: protocol router ───────────────────────────────────────────────

def test_router_normalize_acp():
    order = normalize_acp(ACP_PAYLOAD, buyer_dnsid="dnsid://x/agents/y")
    assert order.protocol        == "acp"
    assert order.buyer_id        == BUYER_ID
    assert order.order_lines[0]["sku"]      == "PPR-001"
    assert order.order_lines[0]["quantity"] == 1
    assert order.buyer_dnsid     == "dnsid://x/agents/y"
    assert order.origin_zip      == "10001"
    assert order.destination_zip == "90210"
    print(f"  {PASS} router_normalize_acp: ACP payload normalized, protocol=acp")


def test_router_normalize_ucp():
    order = normalize_ucp_task(UCP_PAYLOAD)
    assert order.protocol        == "ucp"
    assert order.buyer_id        == BUYER_ID
    assert order.order_lines[0]["sku"]      == "PPR-001"
    assert order.order_lines[0]["quantity"] == 1
    assert order.origin_zip      == "10001"
    assert order.destination_zip == "90210"
    print(f"  {PASS} router_normalize_ucp: UCP payload normalized, protocol=ucp")


# ── Integration tests: live seller server ─────────────────────────────────────

def _start_seller():
    proc = subprocess.Popen(
        [sys.executable, "src/seller_agent/server.py"],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(30):
        try:
            r = httpx.get(f"{SELLER_BASE_URL}/.well-known/agent-card.json", timeout=1.0)
            if r.status_code == 200:
                return proc
        except Exception:
            pass
        time.sleep(0.5)
    proc.terminate()
    raise RuntimeError("Seller server did not start in time")


def test_server_integration():
    print("  Starting seller server for integration tests...")
    proc = _start_seller()
    try:
        with httpx.Client(timeout=10.0) as client:

            # Test 3: ACP checkout returns 201, protocol_of_record=acp
            r = client.post(f"{SELLER_BASE_URL}/acp/v1/checkout", json=ACP_PAYLOAD)
            assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
            data = r.json()
            assert data["protocol_of_record"]          == "acp"
            assert data["result"]["protocol_of_record"] == "acp"
            assert data["status"]                       == "completed"
            print(f"  {PASS} acp_checkout: 201, protocol_of_record=acp in task and result")

            # Test 4: ACP checkout with revoked DNSid returns 403
            r = client.post(
                f"{SELLER_BASE_URL}/acp/v1/checkout",
                json=ACP_PAYLOAD,
                headers={"X-Agent-DNSid": _TEST_REVOKED_HANDLE},
            )
            assert r.status_code == 403, f"Expected 403, got {r.status_code}"
            print(f"  {PASS} acp_revoked_dnsid: 403 returned for revoked DNSid on ACP endpoint")

            # Test 5: UCP /tasks/send still works, protocol_of_record=ucp
            r = client.post(f"{SELLER_BASE_URL}/tasks/send", json=UCP_PAYLOAD)
            assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
            data = r.json()
            assert data["protocol_of_record"]          == "ucp"
            assert data["result"]["protocol_of_record"] == "ucp"
            print(f"  {PASS} ucp_task_send: 201, protocol_of_record=ucp")

            # Test 6: both protocols present in tasks
            acp_protocol = r.json()  # last ucp response
            assert acp_protocol["protocol_of_record"] == "ucp"
            print(f"  {PASS} protocol_of_record_field: present in both ACP and UCP responses")

            # Test 7: governance protocol breakdown
            # Start governance dashboard alongside seller
            gov_proc = subprocess.Popen(
                [sys.executable, "src/governance/dashboard.py"],
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                gov_url = "http://localhost:8085"
                for _ in range(30):
                    try:
                        rg = client.get(f"{gov_url}/governance/summary", timeout=1.0)
                        if rg.status_code == 200:
                            break
                    except Exception:
                        pass
                    time.sleep(0.5)

                r = client.get(f"{gov_url}/governance/protocols")
                assert r.status_code == 200
                data = r.json()
                assert data["total_completed"] >= 2
                assert data["by_protocol"]["acp"] >= 1
                assert data["by_protocol"]["ucp"] >= 1
                protocols_seen = {t["protocol_of_record"] for t in data["transactions"]}
                assert "acp" in protocols_seen
                assert "ucp" in protocols_seen
                print(f"  {PASS} governance_protocols: both acp and ucp recorded in audit trail")

            finally:
                gov_proc.terminate()
                gov_proc.wait()

            # Test 8: ACP gate -- valid DNSid passes
            r = client.post(
                f"{SELLER_BASE_URL}/acp/v1/checkout",
                json=ACP_PAYLOAD,
                headers={"X-Agent-DNSid": "dnsid://supplymind.localhost/agents/procurement-001"},
            )
            assert r.status_code == 201
            assert r.json()["result"]["buyer_dnsid_verified"] is True
            print(f"  {PASS} acp_valid_dnsid: 201, buyer_dnsid_verified=True on ACP endpoint")

            # Test 9: ACP Cart Mandate gate
            op_key, _ = generate_keypair()
            ag_key, _ = generate_keypair()
            INTENT_MANDATES.clear(); CART_MANDATES.clear()
            intent = create_intent_mandate(
                operator_id="cfo@acme.example", buyer_agent_id=BUYER_ID,
                approved_sellers=[SELLER_ID], max_per_tx_usd=500.0,
                max_total_usd=5000.0, private_key=op_key,
            )
            cart = create_cart_mandate(
                intent_mandate_id=intent["mandate_id"], seller_id=SELLER_ID,
                amount_usd=14.99, order_lines=[{"sku": "PPR-001", "quantity": 1}],
                private_key=ag_key,
            )
            cart_with_intent = {**cart, "intent_mandate": intent}

            r = client.post(
                f"{SELLER_BASE_URL}/acp/v1/checkout",
                json={**ACP_PAYLOAD, "cart_mandate": cart_with_intent},
            )
            assert r.status_code == 201
            assert r.json()["result"]["cart_mandate_verified"] is True
            assert r.json()["protocol_of_record"] == "acp"
            print(f"  {PASS} acp_cart_mandate: 201, cart_mandate_verified=True on ACP endpoint")

    finally:
        proc.terminate()
        proc.wait()


def run():
    print()
    print("=" * 60)
    print("Phase 12 Multi-Protocol Checkout Tests")
    print("=" * 60)
    print()

    print("Unit tests (protocol router):")
    test_router_normalize_acp()
    test_router_normalize_ucp()

    print()
    print("Integration tests (live seller server):")
    test_server_integration()

    print()
    print("All Phase 12 tests passed.")
    print()


if __name__ == "__main__":
    run()
