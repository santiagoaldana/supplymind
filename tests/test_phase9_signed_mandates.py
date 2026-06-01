"""
Phase 9 -- AP2 v0.2.0 Signed Mandates: Unit Tests

Tests cover:
  1. Create Intent Mandate, verify signature is present and valid
  2. Create Cart Mandate linked to Intent Mandate, verify signature
  3. Full chain verification: accept when both signatures valid
  4. Reject when Cart Mandate signature is tampered
  5. Reject when Intent Mandate signature is tampered
  6. Reject when Cart amount exceeds Intent Mandate per-tx limit
  7. Reject when seller not in Intent Mandate approved list
  8. Cart Mandate with buyer DNSid -- field propagates to verification result
  9. Cart Mandate creation fails if Intent Mandate not found

Run:
  python tests/test_phase9_signed_mandates.py
"""

import sys
import copy
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.identity.keys import generate_keypair
from src.identity.signed_mandate import (
    create_intent_mandate,
    create_cart_mandate,
    verify_cart_mandate,
    INTENT_MANDATES,
    CART_MANDATES,
)

PASS = "[PASS]"
FAIL = "[FAIL]"

SELLER_ID = "did:web:localhost:8080"
BUYER_ID  = "did:web:localhost:8090"


def _clear():
    INTENT_MANDATES.clear()
    CART_MANDATES.clear()


def test_intent_mandate_created_and_signed():
    _clear()
    operator_key, _ = generate_keypair()

    intent = create_intent_mandate(
        operator_id      = "cfo@acme.example",
        buyer_agent_id   = BUYER_ID,
        approved_sellers = [SELLER_ID],
        max_per_tx_usd   = 500.0,
        max_total_usd    = 5000.0,
        private_key      = operator_key,
    )

    assert "mandate_id"  in intent
    assert "proof"       in intent
    assert "signature"   in intent["proof"]
    assert intent["schema"] == "ap2:intent-mandate:v0.2.0"
    assert intent["proof"]["type"] == "secp256k1-sha256"

    print(f"  {PASS} intent_mandate_created: schema, proof, and signature present")
    return intent, operator_key


def test_cart_mandate_created_and_signed():
    _clear()
    operator_key, _ = generate_keypair()
    agent_key, _    = generate_keypair()

    intent = create_intent_mandate(
        operator_id      = "cfo@acme.example",
        buyer_agent_id   = BUYER_ID,
        approved_sellers = [SELLER_ID],
        max_per_tx_usd   = 500.0,
        max_total_usd    = 5000.0,
        private_key      = operator_key,
    )

    cart = create_cart_mandate(
        intent_mandate_id = intent["mandate_id"],
        seller_id         = SELLER_ID,
        amount_usd        = 150.0,
        order_lines       = [{"sku": "PPR-001", "quantity": 5}],
        private_key       = agent_key,
    )

    assert "cart_mandate_id"   in cart
    assert "proof"             in cart
    assert "signature"         in cart["proof"]
    assert cart["schema"]      == "ap2:cart-mandate:v0.2.0"
    assert cart["intent_mandate_id"] == intent["mandate_id"]

    print(f"  {PASS} cart_mandate_created: linked to intent, proof and signature present")
    return cart, intent


def test_full_chain_verification_accept():
    _clear()
    operator_key, _ = generate_keypair()
    agent_key, _    = generate_keypair()

    intent = create_intent_mandate(
        operator_id      = "cfo@acme.example",
        buyer_agent_id   = BUYER_ID,
        approved_sellers = [SELLER_ID],
        max_per_tx_usd   = 500.0,
        max_total_usd    = 5000.0,
        private_key      = operator_key,
    )
    cart = create_cart_mandate(
        intent_mandate_id = intent["mandate_id"],
        seller_id         = SELLER_ID,
        amount_usd        = 150.0,
        order_lines       = [{"sku": "PPR-001", "quantity": 5}],
        private_key       = agent_key,
    )

    result = verify_cart_mandate(cart)
    assert result["decision"]        == "accept", f"Expected accept, got: {result}"
    assert result["intent_verified"] is True
    assert result["cart_verified"]   is True

    print(f"  {PASS} full_chain_verification: both signatures valid, decision=accept")


def test_reject_tampered_cart_signature():
    _clear()
    operator_key, _ = generate_keypair()
    agent_key, _    = generate_keypair()

    intent = create_intent_mandate(
        operator_id      = "cfo@acme.example",
        buyer_agent_id   = BUYER_ID,
        approved_sellers = [SELLER_ID],
        max_per_tx_usd   = 500.0,
        max_total_usd    = 5000.0,
        private_key      = operator_key,
    )
    cart = create_cart_mandate(
        intent_mandate_id = intent["mandate_id"],
        seller_id         = SELLER_ID,
        amount_usd        = 150.0,
        order_lines       = [{"sku": "PPR-001", "quantity": 5}],
        private_key       = agent_key,
    )

    tampered = copy.deepcopy(cart)
    tampered["amount_usd"] = 9999.0

    result = verify_cart_mandate(tampered)
    assert result["decision"] == "reject"
    assert "signature" in result["reason"].lower() or "invalid" in result["reason"].lower()

    print(f"  {PASS} reject_tampered_cart: amount modified, signature fails")


def test_reject_tampered_intent_signature():
    _clear()
    operator_key, _ = generate_keypair()
    agent_key, _    = generate_keypair()

    intent = create_intent_mandate(
        operator_id      = "cfo@acme.example",
        buyer_agent_id   = BUYER_ID,
        approved_sellers = [SELLER_ID],
        max_per_tx_usd   = 500.0,
        max_total_usd    = 5000.0,
        private_key      = operator_key,
    )

    INTENT_MANDATES[intent["mandate_id"]]["max_per_tx_usd"] = 9999.0

    cart = create_cart_mandate(
        intent_mandate_id = intent["mandate_id"],
        seller_id         = SELLER_ID,
        amount_usd        = 150.0,
        order_lines       = [{"sku": "PPR-001", "quantity": 5}],
        private_key       = agent_key,
    )

    result = verify_cart_mandate(cart)
    assert result["decision"] == "reject"
    assert "intent" in result["reason"].lower()

    print(f"  {PASS} reject_tampered_intent: intent mandate modified, signature fails")


def test_reject_amount_exceeds_per_tx_limit():
    _clear()
    operator_key, _ = generate_keypair()
    agent_key, _    = generate_keypair()

    intent = create_intent_mandate(
        operator_id      = "cfo@acme.example",
        buyer_agent_id   = BUYER_ID,
        approved_sellers = [SELLER_ID],
        max_per_tx_usd   = 100.0,
        max_total_usd    = 5000.0,
        private_key      = operator_key,
    )

    cart = create_cart_mandate(
        intent_mandate_id = intent["mandate_id"],
        seller_id         = SELLER_ID,
        amount_usd        = 250.0,
        order_lines       = [{"sku": "PPR-001", "quantity": 10}],
        private_key       = agent_key,
    )

    assert "error" in cart
    assert "per-tx limit" in cart["error"]

    print(f"  {PASS} reject_exceeds_limit: cart creation blocked when amount > per-tx limit")


def test_reject_seller_not_approved():
    _clear()
    operator_key, _ = generate_keypair()
    agent_key, _    = generate_keypair()

    intent = create_intent_mandate(
        operator_id      = "cfo@acme.example",
        buyer_agent_id   = BUYER_ID,
        approved_sellers = ["did:web:other-seller.example"],
        max_per_tx_usd   = 500.0,
        max_total_usd    = 5000.0,
        private_key      = operator_key,
    )

    cart = create_cart_mandate(
        intent_mandate_id = intent["mandate_id"],
        seller_id         = SELLER_ID,
        amount_usd        = 50.0,
        order_lines       = [{"sku": "PPR-001", "quantity": 2}],
        private_key       = agent_key,
    )

    assert "error" in cart
    assert "approved list" in cart["error"]

    print(f"  {PASS} reject_seller_not_approved: cart creation blocked when seller not in intent mandate")


def test_cart_with_buyer_dnsid():
    _clear()
    operator_key, _ = generate_keypair()
    agent_key, _    = generate_keypair()

    dnsid = "dnsid://supplymind.localhost/agents/procurement-001"

    intent = create_intent_mandate(
        operator_id      = "cfo@acme.example",
        buyer_agent_id   = BUYER_ID,
        approved_sellers = [SELLER_ID],
        max_per_tx_usd   = 500.0,
        max_total_usd    = 5000.0,
        private_key      = operator_key,
        buyer_dnsid      = dnsid,
    )
    cart = create_cart_mandate(
        intent_mandate_id = intent["mandate_id"],
        seller_id         = SELLER_ID,
        amount_usd        = 75.0,
        order_lines       = [{"sku": "PPR-001", "quantity": 3}],
        private_key       = agent_key,
        buyer_dnsid       = dnsid,
    )

    result = verify_cart_mandate(cart)
    assert result["decision"]    == "accept"
    assert result["buyer_dnsid"] == dnsid

    print(f"  {PASS} cart_with_buyer_dnsid: dnsid propagates through chain, decision=accept")


def test_cart_fails_without_intent():
    _clear()
    agent_key, _ = generate_keypair()

    cart = create_cart_mandate(
        intent_mandate_id = "nonexistent-id",
        seller_id         = SELLER_ID,
        amount_usd        = 50.0,
        order_lines       = [{"sku": "PPR-001", "quantity": 2}],
        private_key       = agent_key,
    )

    assert "error" in cart
    assert "not found" in cart["error"]

    print(f"  {PASS} cart_fails_without_intent: cart creation blocked when intent not found")


def run():
    print()
    print("=" * 60)
    print("Phase 9 AP2 v0.2.0 Signed Mandates Tests")
    print("=" * 60)
    print()

    test_intent_mandate_created_and_signed()
    test_cart_mandate_created_and_signed()
    test_full_chain_verification_accept()
    test_reject_tampered_cart_signature()
    test_reject_tampered_intent_signature()
    test_reject_amount_exceeds_per_tx_limit()
    test_reject_seller_not_approved()
    test_cart_with_buyer_dnsid()
    test_cart_fails_without_intent()

    print()
    print("All Phase 9 tests passed.")
    print()


if __name__ == "__main__":
    run()
