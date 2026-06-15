"""
Sardine fraud scoring client for Phase 15.

Sardine is agent-aware: designed for crypto/fintech patterns where
behavioral biometrics don't exist and transaction velocity is expected to be high.

Real API: https://docs.sardine.ai/
Endpoint: POST https://api.sardine.ai/v1/transactions/score
Auth: Bearer token (SARDINE_CLIENT_ID + SARDINE_SECRET_KEY -> OAuth2)

Mock mode (SARDINE_MOCK=true or keys absent): scores locally using rule-based
heuristics that mirror Sardine's documented signal categories.

Signal categories used:
  - Identity signals: DNSid status, known agent vs unknown
  - Velocity signals: request rate, order value, quantity
  - Behavior signals: time of day, endpoint pattern (from rate limiter)
  - Network signals: IP reputation (mocked as clean in test mode)
"""

import os
import time
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv

load_dotenv()

SARDINE_CLIENT_ID  = os.getenv("SARDINE_CLIENT_ID", "")
SARDINE_SECRET_KEY = os.getenv("SARDINE_SECRET_KEY", "")
SARDINE_MOCK       = os.getenv("SARDINE_MOCK", "true").lower() == "true" or not (SARDINE_CLIENT_ID and SARDINE_SECRET_KEY)

SARDINE_TOKEN_URL  = "https://api.sardine.ai/v1/auth/token"
SARDINE_SCORE_URL  = "https://api.sardine.ai/v1/transactions/score"

SCORE_BLOCK_THRESHOLD  = 80   # score >= 80: block
SCORE_REVIEW_THRESHOLD = 50   # score >= 50: flag for review, allow


@dataclass
class SardineScore:
    score: int                  # 0-100, higher = more suspicious
    level: str                  # "low" | "medium" | "high" | "very_high"
    decision: str               # "allow" | "review" | "block"
    signals: list[str]          # human-readable signal descriptions
    mock: bool = False


def _level_from_score(score: int) -> str:
    if score >= SCORE_BLOCK_THRESHOLD:
        return "very_high"
    if score >= SCORE_REVIEW_THRESHOLD:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def _decision_from_score(score: int) -> str:
    if score >= SCORE_BLOCK_THRESHOLD:
        return "block"
    if score >= SCORE_REVIEW_THRESHOLD:
        return "review"
    return "allow"


def _mock_score(
    agent_dnsid: str | None,
    dnsid_status: str,
    order_value_usd: float,
    quantity: int,
    request_count_per_minute: int,
    buyer_id: str,
) -> SardineScore:
    """
    Rule-based scoring that mirrors Sardine's documented signal categories.
    Used when SARDINE_MOCK=true or API keys are absent.
    """
    score = 0
    signals = []

    # Identity signals
    if not agent_dnsid:
        score += 20
        signals.append("no_dnsid: agent has no identity anchor")
    elif dnsid_status == "revoked":
        score += 80
        signals.append("dnsid_revoked: identity credential is revoked")
    elif dnsid_status == "active":
        score -= 10
        signals.append("dnsid_verified: known identity anchor")

    # Velocity signals
    if order_value_usd > 5000:
        score += 25
        signals.append(f"high_order_value: ${order_value_usd:.2f}")
    elif order_value_usd > 2000:
        score += 10
        signals.append(f"elevated_order_value: ${order_value_usd:.2f}")

    if quantity > 500:
        score += 20
        signals.append(f"high_quantity: {quantity} units")

    if request_count_per_minute > 150:
        score += 30
        signals.append(f"high_velocity: {request_count_per_minute} req/min")
    elif request_count_per_minute > 100:
        score += 15
        signals.append(f"elevated_velocity: {request_count_per_minute} req/min")

    # Unknown buyer with high order value is elevated risk
    if not agent_dnsid and order_value_usd > 500:
        score += 15
        signals.append("anonymous_high_value: no identity + high order value")

    score = max(0, min(100, score))

    return SardineScore(
        score=score,
        level=_level_from_score(score),
        decision=_decision_from_score(score),
        signals=signals,
        mock=True,
    )


def _get_sardine_token() -> str:
    resp = httpx.post(
        SARDINE_TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(SARDINE_CLIENT_ID, SARDINE_SECRET_KEY),
        timeout=5.0,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def score_transaction(
    agent_dnsid: str | None,
    dnsid_status: str,
    order_value_usd: float,
    quantity: int,
    request_count_per_minute: int,
    buyer_id: str,
    client_ip: str = "unknown",
) -> SardineScore:
    """
    Score an incoming transaction request.
    Falls back to mock scoring if API keys are absent or SARDINE_MOCK=true.
    """
    if SARDINE_MOCK:
        return _mock_score(
            agent_dnsid=agent_dnsid,
            dnsid_status=dnsid_status,
            order_value_usd=order_value_usd,
            quantity=quantity,
            request_count_per_minute=request_count_per_minute,
            buyer_id=buyer_id,
        )

    try:
        token = _get_sardine_token()
        payload = {
            "sessionKey": f"{buyer_id}:{int(time.time())}",
            "customer": {
                "id": buyer_id,
                "type": "agent",
            },
            "transaction": {
                "id": f"tx-{int(time.time())}",
                "type": "purchase",
                "currencyCode": "USD",
                "amount": order_value_usd,
                "itemCount": quantity,
            },
            "agent": {
                "dnsid": agent_dnsid,
                "dnsid_status": dnsid_status,
                "request_rate_per_minute": request_count_per_minute,
            },
            "device": {
                "ip": client_ip,
            },
        }
        resp = httpx.post(
            SARDINE_SCORE_URL,
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5.0,
        )
        resp.raise_for_status()
        data = resp.json()
        raw_score = data.get("score", 0)
        return SardineScore(
            score=raw_score,
            level=_level_from_score(raw_score),
            decision=_decision_from_score(raw_score),
            signals=data.get("signals", []),
            mock=False,
        )
    except Exception:
        # Sardine API unavailable: fail open with mock score.
        # In production this would be a configurable fail-open vs fail-closed policy.
        return _mock_score(
            agent_dnsid=agent_dnsid,
            dnsid_status=dnsid_status,
            order_value_usd=order_value_usd,
            quantity=quantity,
            request_count_per_minute=request_count_per_minute,
            buyer_id=buyer_id,
        )
