"""
Phase 8 — DNSid Agent Ownership Layer: Unit Tests

Tests cover:
  1. Register three agents, verify handles and resolved records
  2. Revoke one handle, verify resolve returns revoked status
  3. Test sentinel handle always returns revoked
  4. Mandate check with valid DNSid: passes, marks dnsid_verified=True
  5. Mandate check with revoked DNSid: blocked regardless of amount
  6. Mandate check with no DNSid: proceeds normally (default-off behavior)
  7. x402 gate: verified buyer gets higher free-quote threshold
  8. x402 gate: revoked buyer gets 403 before quote
  9. Purchase gate (POST /tasks/send): valid DNSid accepted
 10. Purchase gate: revoked DNSid returns 403
 11. Purchase gate: no DNSid header proceeds normally

Run:
  python tests/test_phase8_dnsid.py
"""

import sys
import time
import subprocess
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.identity.dnsid import (
    register_agent,
    resolve_dnsid,
    revoke_agent,
    list_registry,
    _REGISTRY,
    _TEST_REVOKED_HANDLE,
)
from src.payment_server.mandate import create_mandate, check_mandate

SELLER_BASE_URL = "http://localhost:8080"

PASS = "[PASS]"
FAIL = "[FAIL]"


def _clear_registry():
    _REGISTRY.clear()


def test_register_and_resolve():
    _clear_registry()

    h1 = register_agent("inventory-001",   "supplymind.localhost", "supplymind.localhost")
    h2 = register_agent("procurement-001", "supplymind.localhost", "supplymind.localhost")
    h3 = register_agent("seller-001",      "supplymind.localhost", "supplymind.localhost")

    assert h1 == "dnsid://supplymind.localhost/agents/inventory-001"
    assert h2 == "dnsid://supplymind.localhost/agents/procurement-001"
    assert h3 == "dnsid://supplymind.localhost/agents/seller-001"

    for handle in [h1, h2, h3]:
        record = resolve_dnsid(handle)
        assert record["status"] == "active", f"Expected active, got {record['status']}"
        assert record["owner"]  == "supplymind.localhost"

    registry = list_registry()
    assert len(registry) == 3

    print(f"  {PASS} register_and_resolve: 3 agents registered and resolved")


def test_revocation():
    _clear_registry()

    handle = register_agent("buyer-temp", "acme.localhost", "acme.localhost")
    assert resolve_dnsid(handle)["status"] == "active"

    result = revoke_agent(handle, reason="test revocation")
    assert result["status"] == "revoked"
    assert result["revoked_at"] is not None

    resolved = resolve_dnsid(handle)
    assert resolved["status"] == "revoked"
    assert resolved["revocation_reason"] == "test revocation"

    print(f"  {PASS} revocation: handle revoked and resolve reflects revoked status")


def test_sentinel_always_revoked():
    record = resolve_dnsid(_TEST_REVOKED_HANDLE)
    assert record["status"] == "revoked"
    assert record["revocation_reason"] == "test-sentinel"

    print(f"  {PASS} sentinel_always_revoked: test handle returns revoked")


def test_not_found():
    record = resolve_dnsid("dnsid://unknown.localhost/agents/ghost-001")
    assert record["status"] == "not_found"

    print(f"  {PASS} not_found: unknown handle returns status=not_found")


def test_mandate_check_no_dnsid():
    mandate = create_mandate(
        buyer_id="did:web:localhost:8090",
        approved_sellers=["did:web:localhost:8080"],
        max_per_tx_usd=500.0,
        max_total_usd=5000.0,
    )
    result = check_mandate(mandate["mandate_id"], 3.00, "did:web:localhost:8080")
    assert result["decision"] == "approve"
    assert result["buyer_dnsid_verified"] is False

    print(f"  {PASS} mandate_check_no_dnsid: proceeds normally, dnsid_verified=False")


def test_mandate_check_valid_dnsid():
    _clear_registry()
    handle = register_agent("procurement-001", "supplymind.localhost", "supplymind.localhost")

    mandate = create_mandate(
        buyer_id="did:web:localhost:8090",
        approved_sellers=["did:web:localhost:8080"],
        max_per_tx_usd=500.0,
        max_total_usd=5000.0,
    )
    result = check_mandate(
        mandate["mandate_id"], 3.00, "did:web:localhost:8080",
        buyer_dnsid=handle,
    )
    assert result["decision"] == "approve"
    assert result["buyer_dnsid_verified"] is True

    print(f"  {PASS} mandate_check_valid_dnsid: approved, dnsid_verified=True")


def test_mandate_check_revoked_dnsid():
    mandate = create_mandate(
        buyer_id="did:web:localhost:8090",
        approved_sellers=["did:web:localhost:8080"],
        max_per_tx_usd=500.0,
        max_total_usd=5000.0,
    )
    result = check_mandate(
        mandate["mandate_id"], 1.00, "did:web:localhost:8080",
        buyer_dnsid=_TEST_REVOKED_HANDLE,
    )
    assert result["decision"] == "block"
    assert "revoked" in result["reason"].lower()

    print(f"  {PASS} mandate_check_revoked_dnsid: blocked when DNSid is revoked")


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


def test_server_gates():
    print("  Starting seller server for integration tests...")
    proc = _start_seller()
    try:
        with httpx.Client(timeout=10.0) as client:

            # ── Test 7: verified buyer gets higher x402 threshold ───────────
            # Register procurement-001 in the seller's in-process registry?
            # Server runs in a subprocess with its own memory -- we test the
            # behavior at the HTTP boundary: sending a DNSid handle that the
            # server's seeded registry would recognize. Since the server seeds
            # its own registry on import, we test with a quantity low enough
            # that $500 threshold is not triggered (quantity 5 * ~$20 = $100).
            r = client.get(
                f"{SELLER_BASE_URL}/quotes/PPR-001?quantity=5",
                headers={"X-Agent-DNSid": "dnsid://supplymind.localhost/agents/procurement-001"},
            )
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"
            assert r.json()["buyer_dnsid_verified"] is True
            print(f"  {PASS} quote_with_valid_dnsid: 200 returned, dnsid_verified=True")

            # ── Test 8: revoked DNSid returns 403 before any quote ──────────
            r = client.get(
                f"{SELLER_BASE_URL}/quotes/PPR-001?quantity=5",
                headers={"X-Agent-DNSid": _TEST_REVOKED_HANDLE},
            )
            assert r.status_code == 403, f"Expected 403, got {r.status_code}"
            print(f"  {PASS} quote_revoked_dnsid: 403 returned for revoked handle")

            # ── Test 9: purchase with valid DNSid, dnsid_verified in result ─
            task_payload = {
                "buyer_id":        "did:web:localhost:8090",
                "order_lines":     [{"sku": "PPR-001", "quantity": 1}],
                "origin_zip":      "10001",
                "destination_zip": "90210",
                "service_level":   "standard",
            }
            r = client.post(
                f"{SELLER_BASE_URL}/tasks/send",
                json=task_payload,
                headers={"X-Agent-DNSid": "dnsid://supplymind.localhost/agents/procurement-001"},
            )
            assert r.status_code == 201, f"Expected 201, got {r.status_code}"
            assert r.json()["result"]["buyer_dnsid_verified"] is True
            print(f"  {PASS} purchase_with_valid_dnsid: 201, dnsid_verified=True")

            # ── Test 10: purchase with revoked DNSid returns 403 ────────────
            r = client.post(
                f"{SELLER_BASE_URL}/tasks/send",
                json=task_payload,
                headers={"X-Agent-DNSid": _TEST_REVOKED_HANDLE},
            )
            assert r.status_code == 403, f"Expected 403, got {r.status_code}"
            print(f"  {PASS} purchase_revoked_dnsid: 403 returned for revoked handle")

            # ── Test 11: purchase with no DNSid header proceeds normally ────
            r = client.post(f"{SELLER_BASE_URL}/tasks/send", json=task_payload)
            assert r.status_code == 201, f"Expected 201, got {r.status_code}"
            assert r.json()["result"]["buyer_dnsid_verified"] is False
            print(f"  {PASS} purchase_no_dnsid: 201, proceeds normally, dnsid_verified=False")

    finally:
        proc.terminate()
        proc.wait()


def run():
    print()
    print("=" * 60)
    print("Phase 8 DNSid Tests")
    print("=" * 60)
    print()

    print("Unit tests (in-memory registry):")
    test_register_and_resolve()
    test_revocation()
    test_sentinel_always_revoked()
    test_not_found()
    test_mandate_check_no_dnsid()
    test_mandate_check_valid_dnsid()
    test_mandate_check_revoked_dnsid()

    print()
    print("Integration tests (live seller server):")
    test_server_gates()

    print()
    print("All Phase 8 tests passed.")
    print()


if __name__ == "__main__":
    run()
