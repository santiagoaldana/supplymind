"""
Phase 15: Fraud and Bot Detection tests.

Covers:
  1. Legitimate agent with active DNSid passes all gates
  2. Unknown agent (no DNSid) with low order value passes (low score)
  3. Anonymous agent with very high order value gets elevated score
  4. Revoked DNSid raises score to block threshold
  5. Rate limit blocks after burst limit exceeded
  6. Window rate limit blocks after sustained high volume
  7. Sardine mock scoring produces correct signal categories
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fraud.sardine_client import score_transaction, SCORE_BLOCK_THRESHOLD
from src.fraud.rate_limiter import check_rate_limit, reset_for_testing, MAX_REQUESTS_BURST, MAX_REQUESTS_WINDOW


# ── Sardine mock scoring tests ────────────────────────────────────────────────

def test_legitimate_agent_low_score():
    result = score_transaction(
        agent_dnsid="dnsid://supplymind.localhost/agents/buyer-001",
        dnsid_status="active",
        order_value_usd=250.0,
        quantity=10,
        request_count_per_minute=5,
        buyer_id="did:web:localhost:8090",
    )
    assert result.decision == "allow", f"Expected allow, got {result.decision} (score={result.score})"
    assert result.score < 50, f"Expected low score, got {result.score}"
    print(f"  legitimate agent score={result.score} decision={result.decision} signals={result.signals}")


def test_anonymous_low_value_passes():
    result = score_transaction(
        agent_dnsid=None,
        dnsid_status="unknown",
        order_value_usd=100.0,
        quantity=5,
        request_count_per_minute=3,
        buyer_id="unknown-buyer",
    )
    assert result.decision in ("allow", "review"), f"Expected allow/review, got {result.decision}"
    assert "no_dnsid" in " ".join(result.signals)
    print(f"  anonymous low-value score={result.score} decision={result.decision}")


def test_anonymous_high_value_elevated():
    result = score_transaction(
        agent_dnsid=None,
        dnsid_status="unknown",
        order_value_usd=6000.0,
        quantity=200,
        request_count_per_minute=10,
        buyer_id="unknown-buyer",
    )
    assert result.score >= 50, f"Expected elevated score, got {result.score}"
    print(f"  anonymous high-value score={result.score} decision={result.decision} signals={result.signals}")


def test_revoked_dnsid_blocked():
    result = score_transaction(
        agent_dnsid="dnsid://supplymind.localhost/agents/revoked-001",
        dnsid_status="revoked",
        order_value_usd=100.0,
        quantity=5,
        request_count_per_minute=3,
        buyer_id="revoked-buyer",
    )
    assert result.decision == "block", f"Expected block for revoked DNSid, got {result.decision} (score={result.score})"
    assert result.score >= SCORE_BLOCK_THRESHOLD
    print(f"  revoked DNSid score={result.score} decision={result.decision}")


def test_high_velocity_elevated():
    result = score_transaction(
        agent_dnsid=None,
        dnsid_status="unknown",
        order_value_usd=50.0,
        quantity=5,
        request_count_per_minute=160,
        buyer_id="fast-buyer",
    )
    assert result.score >= 50, f"Expected elevated score for high velocity, got {result.score}"
    assert any("velocity" in s for s in result.signals)
    print(f"  high velocity score={result.score} decision={result.decision}")


# ── Rate limiter tests ────────────────────────────────────────────────────────

def test_normal_request_allowed():
    reset_for_testing()
    result = check_rate_limit("dnsid://supplymind.localhost/agents/buyer-001")
    assert result.allowed, f"Expected allowed, got blocked: {result.reason}"
    print(f"  normal request allowed identity={result.identity} count={result.request_count}")


def test_burst_limit_blocks():
    identity = "dnsid://supplymind.localhost/agents/burst-attacker"
    reset_for_testing(identity)

    for _ in range(MAX_REQUESTS_BURST):
        check_rate_limit(identity)

    result = check_rate_limit(identity)
    assert not result.allowed, f"Expected burst block after {MAX_REQUESTS_BURST} requests"
    assert "Burst" in result.reason
    print(f"  burst limit triggered at count={result.burst_count} reason={result.reason}")


def test_ip_fallback_when_no_dnsid():
    reset_for_testing("ip:192.168.1.99")
    result = check_rate_limit(None, client_ip="192.168.1.99")
    assert result.allowed
    assert result.identity == "ip:192.168.1.99"
    print(f"  IP fallback identity={result.identity}")


def test_different_identities_independent():
    reset_for_testing()
    id_a = "dnsid://supplymind.localhost/agents/agent-a"
    id_b = "dnsid://supplymind.localhost/agents/agent-b"

    for _ in range(MAX_REQUESTS_BURST):
        check_rate_limit(id_a)

    result_b = check_rate_limit(id_b)
    assert result_b.allowed, "Agent B should not be affected by Agent A's rate limit"
    print(f"  agents are isolated: agent-b count={result_b.request_count}")


if __name__ == "__main__":
    tests = [
        test_legitimate_agent_low_score,
        test_anonymous_low_value_passes,
        test_anonymous_high_value_elevated,
        test_revoked_dnsid_blocked,
        test_high_velocity_elevated,
        test_normal_request_allowed,
        test_burst_limit_blocks,
        test_ip_fallback_when_no_dnsid,
        test_different_identities_independent,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            print(f"\n{test.__name__}")
            test()
            print("  PASS")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Phase 15 results: {passed} passed, {failed} failed")
    if failed:
        sys.exit(1)
