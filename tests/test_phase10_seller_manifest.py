"""
Phase 10 -- Seller Authorization Manifest: Unit + Integration Tests

Tests cover:
  1. Create Seller Manifest, verify signature present and valid
  2. Create Signed Offer within manifest bounds, verify signature
  3. Full chain verification: accept when both signatures valid
  4. Reject when offer price above manifest maximum
  5. Reject when offer price below manifest minimum
  6. Reject when discount exceeds manifest limit
  7. Reject when SKU not in manifest
  8. Reject when offer signature tampered
  9. Reject when manifest signature tampered
 10. Signed offer creation blocked when SKU not authorized
 11. Server: GET /.well-known/seller-manifest.json returns signed manifest
 12. Server: GET /quotes/{sku} returns signed_offer embedded in response
 13. Server: signed_offer verifies correctly from quote response

Run:
  python tests/test_phase10_seller_manifest.py
"""

import sys
import copy
import time
import subprocess
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.identity.keys import generate_keypair
from src.identity.seller_manifest import (
    create_seller_manifest,
    create_signed_offer,
    verify_signed_offer,
    SELLER_MANIFESTS,
    SIGNED_OFFERS,
)

PASS = "[PASS]"
FAIL = "[FAIL]"

SELLER_BASE_URL  = "http://localhost:8080"
SELLER_DNSID     = "dnsid://supplymind.localhost/agents/seller-001"
SELLER_AGENT_ID  = "did:web:localhost:8080"

AUTHORIZED_SKUS = [
    {"sku": "PPR-001", "min_price_usd": 5.00, "max_price_usd": 30.00, "max_discount_pct": 5.0},
    {"sku": "PEN-001", "min_price_usd": 1.00, "max_price_usd": 20.00, "max_discount_pct": 3.0},
]


def _clear():
    SELLER_MANIFESTS.clear()
    SIGNED_OFFERS.clear()


def test_manifest_created_and_signed():
    _clear()
    operator_key, _ = generate_keypair()

    manifest = create_seller_manifest(
        operator_id     = "ops@acme.example",
        seller_agent_id = SELLER_AGENT_ID,
        seller_dnsid    = SELLER_DNSID,
        authorized_skus = AUTHORIZED_SKUS,
        private_key     = operator_key,
    )

    assert "manifest_id" in manifest
    assert "proof"       in manifest
    assert "signature"   in manifest["proof"]
    assert manifest["schema"]           == "sam:seller-manifest:v0.1.0"
    assert manifest["proof"]["type"]    == "secp256k1-sha256"
    assert manifest["seller_dnsid"]     == SELLER_DNSID

    print(f"  {PASS} manifest_created: schema, proof, and signature present")
    return manifest, operator_key


def test_signed_offer_created():
    _clear()
    operator_key, _ = generate_keypair()
    agent_key, _    = generate_keypair()

    manifest = create_seller_manifest(
        operator_id     = "ops@acme.example",
        seller_agent_id = SELLER_AGENT_ID,
        seller_dnsid    = SELLER_DNSID,
        authorized_skus = AUTHORIZED_SKUS,
        private_key     = operator_key,
    )

    offer = create_signed_offer(
        manifest_id  = manifest["manifest_id"],
        sku          = "PPR-001",
        quantity     = 10,
        unit_price   = 14.99,
        discount_pct = 2.0,
        private_key  = agent_key,
    )

    assert "offer_id"    in offer
    assert "proof"       in offer
    assert "signature"   in offer["proof"]
    assert offer["schema"]          == "sam:signed-offer:v0.1.0"
    assert offer["manifest_id"]     == manifest["manifest_id"]
    assert offer["sku"]             == "PPR-001"

    print(f"  {PASS} signed_offer_created: linked to manifest, proof present")
    return offer, manifest


def test_full_chain_verification_accept():
    _clear()
    operator_key, _ = generate_keypair()
    agent_key, _    = generate_keypair()

    manifest = create_seller_manifest(
        operator_id     = "ops@acme.example",
        seller_agent_id = SELLER_AGENT_ID,
        seller_dnsid    = SELLER_DNSID,
        authorized_skus = AUTHORIZED_SKUS,
        private_key     = operator_key,
    )
    offer = create_signed_offer(
        manifest_id  = manifest["manifest_id"],
        sku          = "PPR-001",
        quantity     = 10,
        unit_price   = 14.99,
        discount_pct = 2.0,
        private_key  = agent_key,
    )

    result = verify_signed_offer(offer)
    assert result["decision"]          == "accept", f"Expected accept, got: {result}"
    assert result["offer_verified"]    is True
    assert result["manifest_verified"] is True
    assert result["operator_id"]       == "ops@acme.example"

    print(f"  {PASS} full_chain_verification: both signatures valid, decision=accept")


def test_reject_price_above_maximum():
    _clear()
    operator_key, _ = generate_keypair()
    agent_key, _    = generate_keypair()

    manifest = create_seller_manifest(
        operator_id="ops@acme.example", seller_agent_id=SELLER_AGENT_ID,
        seller_dnsid=SELLER_DNSID, authorized_skus=AUTHORIZED_SKUS, private_key=operator_key,
    )
    offer = create_signed_offer(
        manifest_id=manifest["manifest_id"], sku="PPR-001", quantity=1,
        unit_price=99.99, discount_pct=0.0, private_key=agent_key,
    )
    assert "error" in offer
    assert "above manifest maximum" in offer["error"]
    print(f"  {PASS} reject_price_above_max: offer creation blocked")


def test_reject_price_below_minimum():
    _clear()
    operator_key, _ = generate_keypair()
    agent_key, _    = generate_keypair()

    manifest = create_seller_manifest(
        operator_id="ops@acme.example", seller_agent_id=SELLER_AGENT_ID,
        seller_dnsid=SELLER_DNSID, authorized_skus=AUTHORIZED_SKUS, private_key=operator_key,
    )
    offer = create_signed_offer(
        manifest_id=manifest["manifest_id"], sku="PPR-001", quantity=1,
        unit_price=1.00, discount_pct=0.0, private_key=agent_key,
    )
    assert "error" in offer
    assert "below manifest minimum" in offer["error"]
    print(f"  {PASS} reject_price_below_min: offer creation blocked")


def test_reject_discount_exceeds_limit():
    _clear()
    operator_key, _ = generate_keypair()
    agent_key, _    = generate_keypair()

    manifest = create_seller_manifest(
        operator_id="ops@acme.example", seller_agent_id=SELLER_AGENT_ID,
        seller_dnsid=SELLER_DNSID, authorized_skus=AUTHORIZED_SKUS, private_key=operator_key,
    )
    offer = create_signed_offer(
        manifest_id=manifest["manifest_id"], sku="PPR-001", quantity=10,
        unit_price=14.99, discount_pct=20.0, private_key=agent_key,
    )
    assert "error" in offer
    assert "exceeds manifest limit" in offer["error"]
    print(f"  {PASS} reject_discount_exceeds_limit: offer creation blocked")


def test_reject_sku_not_authorized():
    _clear()
    operator_key, _ = generate_keypair()
    agent_key, _    = generate_keypair()

    manifest = create_seller_manifest(
        operator_id="ops@acme.example", seller_agent_id=SELLER_AGENT_ID,
        seller_dnsid=SELLER_DNSID, authorized_skus=AUTHORIZED_SKUS, private_key=operator_key,
    )
    offer = create_signed_offer(
        manifest_id=manifest["manifest_id"], sku="FAKE-999", quantity=1,
        unit_price=10.00, discount_pct=0.0, private_key=agent_key,
    )
    assert "error" in offer
    assert "not authorized" in offer["error"]
    print(f"  {PASS} reject_sku_not_authorized: offer creation blocked for unknown SKU")


def test_reject_tampered_offer_signature():
    _clear()
    operator_key, _ = generate_keypair()
    agent_key, _    = generate_keypair()

    manifest = create_seller_manifest(
        operator_id="ops@acme.example", seller_agent_id=SELLER_AGENT_ID,
        seller_dnsid=SELLER_DNSID, authorized_skus=AUTHORIZED_SKUS, private_key=operator_key,
    )
    offer = create_signed_offer(
        manifest_id=manifest["manifest_id"], sku="PPR-001", quantity=10,
        unit_price=14.99, discount_pct=2.0, private_key=agent_key,
    )

    tampered = copy.deepcopy(offer)
    tampered["unit_price"] = 1.00

    result = verify_signed_offer(tampered)
    assert result["decision"] == "reject"
    assert "signature" in result["reason"].lower() or "invalid" in result["reason"].lower()
    print(f"  {PASS} reject_tampered_offer: price modified, signature fails")


def test_reject_tampered_manifest_signature():
    _clear()
    operator_key, _ = generate_keypair()
    agent_key, _    = generate_keypair()

    manifest = create_seller_manifest(
        operator_id="ops@acme.example", seller_agent_id=SELLER_AGENT_ID,
        seller_dnsid=SELLER_DNSID, authorized_skus=AUTHORIZED_SKUS, private_key=operator_key,
    )

    SELLER_MANIFESTS[manifest["manifest_id"]]["authorized_skus"][0]["max_price_usd"] = 9999.0

    offer = create_signed_offer(
        manifest_id=manifest["manifest_id"], sku="PPR-001", quantity=10,
        unit_price=14.99, discount_pct=2.0, private_key=agent_key,
    )

    result = verify_signed_offer(offer)
    assert result["decision"] == "reject"
    assert "manifest" in result["reason"].lower()
    print(f"  {PASS} reject_tampered_manifest: manifest modified, signature fails")


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


def test_server_manifest_and_signed_quotes():
    print("  Starting seller server for integration tests...")
    proc = _start_seller()
    try:
        with httpx.Client(timeout=10.0) as client:

            # Test 11: manifest endpoint returns signed manifest
            r = client.get(f"{SELLER_BASE_URL}/.well-known/seller-manifest.json")
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"
            manifest = r.json()
            assert manifest["schema"]        == "sam:seller-manifest:v0.1.0"
            assert "proof"                   in manifest
            assert manifest["seller_dnsid"]  == SELLER_DNSID
            print(f"  {PASS} server_manifest_endpoint: 200, signed manifest returned")

            # Test 12: quote response includes signed_offer
            r = client.get(f"{SELLER_BASE_URL}/quotes/PPR-001?quantity=5")
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"
            quote = r.json()
            assert "signed_offer" in quote
            assert quote["signed_offer"] is not None
            assert quote["signed_offer"]["schema"] == "sam:signed-offer:v0.1.0"
            print(f"  {PASS} server_quote_signed_offer: quote includes signed_offer")

            # Test 13: verify the signed offer from the quote response
            signed_offer = quote["signed_offer"]
            result = verify_signed_offer(signed_offer)
            assert result["decision"]          == "accept", f"Expected accept, got: {result}"
            assert result["offer_verified"]    is True
            assert result["manifest_verified"] is True
            assert result["operator_id"]       == "ops@supplymind.localhost"
            print(f"  {PASS} server_offer_verifies: full chain verifies, operator_id=ops@supplymind.localhost")

    finally:
        proc.terminate()
        proc.wait()


def run():
    print()
    print("=" * 60)
    print("Phase 10 Seller Authorization Manifest Tests")
    print("=" * 60)
    print()

    print("Unit tests:")
    test_manifest_created_and_signed()
    test_signed_offer_created()
    test_full_chain_verification_accept()
    test_reject_price_above_maximum()
    test_reject_price_below_minimum()
    test_reject_discount_exceeds_limit()
    test_reject_sku_not_authorized()
    test_reject_tampered_offer_signature()
    test_reject_tampered_manifest_signature()

    print()
    print("Integration tests (live seller server):")
    test_server_manifest_and_signed_quotes()

    print()
    print("All Phase 10 tests passed.")
    print()


if __name__ == "__main__":
    run()
