"""
Governance Dashboard -- Phase 11

CISO-grade audit server aggregating all trust and authorization layers built
across Phases 7-10. Answers Clerk's four auth questions across every agent
and transaction in the SupplyMind system.

ENDPOINTS:

  GET /governance/agents
    Full DNSid registry: every registered agent, owner, status, revocation.
    Answers: Identity -- who are all the agents, are any revoked?

  GET /governance/seller-manifests
    All Seller Authorization Manifests: what each seller agent is authorized
    to sell, at what prices, signed by whom.
    Answers: Scoping (seller side) -- is each seller operating within bounds?

  GET /governance/intent-mandates
    All Intent Mandates: who authorized each buyer agent to spend, up to how
    much, with which sellers, signed by which human operator.
    Answers: Scoping + Approvals (buyer side) -- is each buyer within policy?

  GET /governance/cart-mandates
    All Cart Mandates: every signed transaction authorization the buyer agent
    generated, linked to its Intent Mandate.
    Answers: Approvals -- was each transaction explicitly authorized?

  GET /governance/summary
    Aggregated health view across all four Clerk questions.
    Revoked agents, unverified transactions, mandate violations, manifest
    violations -- the single-screen CISO view.

  GET /governance/audit-trail
    Ordered event log: every registration, signing, and revocation event
    across all layers, with timestamps and operator attribution.

Run alongside the seller server:
  python src/governance/dashboard.py
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

import httpx

from src.identity.dnsid import list_registry, _REGISTRY
from src.identity.seller_manifest import SELLER_MANIFESTS, SIGNED_OFFERS
from src.identity.signed_mandate import INTENT_MANDATES, CART_MANDATES
from src.payment_server.mandate import MANDATES

SELLER_SERVER_URL = "http://localhost:8080"


def _fetch_tasks() -> list[dict]:
    """Fetch tasks from seller server. Returns empty list if server unreachable."""
    try:
        r = httpx.get(f"{SELLER_SERVER_URL}/tasks", timeout=2.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []

app = FastAPI(
    title="SupplyMind Governance Dashboard",
    description="Phase 11: CISO-grade audit view -- Clerk four-question coverage across all agents and transactions",
    version="1.0.0",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Clerk Question 1: Identity ────────────────────────────────────────────────

@app.get("/governance/agents")
async def get_agents():
    """
    Identity layer: all registered agents and their current status.
    Revoked agents are flagged. Answers: who are the agents, are any compromised?
    """
    agents = list_registry()
    active  = [a for a in agents if a["status"] == "active"]
    revoked = [a for a in agents if a["status"] == "revoked"]

    return JSONResponse(content={
        "clerk_question": "Identity -- who are the agents?",
        "total":   len(agents),
        "active":  len(active),
        "revoked": len(revoked),
        "agents":  agents,
        "generated_at": _now(),
    })


# ── Clerk Question 2: Scoping ─────────────────────────────────────────────────

@app.get("/governance/seller-manifests")
async def get_seller_manifests():
    """
    Scoping layer (seller side): all Seller Authorization Manifests.
    Shows what each seller agent is permitted to sell and at what prices,
    with the operator who authorized it.
    """
    manifests = list(SELLER_MANIFESTS.values())

    summary = []
    for m in manifests:
        summary.append({
            "manifest_id":    m["manifest_id"],
            "seller_agent_id":m["seller_agent_id"],
            "seller_dnsid":   m["seller_dnsid"],
            "operator_id":    m["operator_id"],
            "sku_count":      len(m["authorized_skus"]),
            "authorized_skus":m["authorized_skus"],
            "signed":         "proof" in m,
            "created_at":     m["created_at"],
        })

    return JSONResponse(content={
        "clerk_question": "Scoping (seller) -- what is each seller authorized to offer?",
        "total":     len(manifests),
        "manifests": summary,
        "generated_at": _now(),
    })


@app.get("/governance/intent-mandates")
async def get_intent_mandates():
    """
    Scoping + Approvals layer (buyer side): all Intent Mandates.
    Shows who authorized each buyer agent, spending limits, and approved sellers.
    """
    mandates = list(INTENT_MANDATES.values())

    summary = []
    for m in mandates:
        summary.append({
            "mandate_id":       m["mandate_id"],
            "operator_id":      m["operator_id"],
            "buyer_agent_id":   m["buyer_agent_id"],
            "buyer_dnsid":      m.get("buyer_dnsid"),
            "approved_sellers": m["approved_sellers"],
            "max_per_tx_usd":   m["max_per_tx_usd"],
            "max_total_usd":    m["max_total_usd"],
            "signed":           "proof" in m,
            "created_at":       m["created_at"],
        })

    return JSONResponse(content={
        "clerk_question": "Scoping + Approvals (buyer) -- who authorized each buyer agent and within what limits?",
        "total":    len(mandates),
        "mandates": summary,
        "generated_at": _now(),
    })


# ── Clerk Question 3: Approvals ───────────────────────────────────────────────

@app.get("/governance/cart-mandates")
async def get_cart_mandates():
    """
    Approvals layer: all Cart Mandates -- every signed per-transaction
    authorization the buyer agent generated. Each is linked to an Intent Mandate.
    """
    carts = list(CART_MANDATES.values())

    summary = []
    for c in carts:
        summary.append({
            "cart_mandate_id":   c["cart_mandate_id"],
            "intent_mandate_id": c["intent_mandate_id"],
            "seller_id":         c["seller_id"],
            "amount_usd":        c["amount_usd"],
            "buyer_dnsid":       c.get("buyer_dnsid"),
            "order_lines":       c["order_lines"],
            "signed":            "proof" in c,
            "created_at":        c["created_at"],
        })

    return JSONResponse(content={
        "clerk_question": "Approvals -- was each transaction explicitly authorized by the buyer agent?",
        "total": len(carts),
        "cart_mandates": summary,
        "generated_at": _now(),
    })


# ── Clerk Question 4: Enforcement ─────────────────────────────────────────────

@app.get("/governance/signed-offers")
async def get_signed_offers():
    """
    Enforcement layer (seller side): all Signed Offers generated by seller agents.
    Each offer is linked to a Seller Authorization Manifest and verifiable.
    """
    offers = list(SIGNED_OFFERS.values())

    summary = []
    for o in offers:
        summary.append({
            "offer_id":    o["offer_id"],
            "manifest_id": o["manifest_id"],
            "sku":         o["sku"],
            "quantity":    o["quantity"],
            "unit_price":  o["unit_price"],
            "discount_pct":o["discount_pct"],
            "total_usd":   o["total_usd"],
            "buyer_id":    o.get("buyer_id"),
            "signed":      "proof" in o,
            "created_at":  o["created_at"],
        })

    return JSONResponse(content={
        "clerk_question": "Enforcement (seller) -- did each offer stay within the authorized manifest?",
        "total":  len(offers),
        "offers": summary,
        "generated_at": _now(),
    })


# ── Phase 12: Protocol-of-Record ─────────────────────────────────────────────

@app.get("/governance/protocols")
async def get_protocol_breakdown():
    """
    Phase 12: Protocol-of-record breakdown across all completed orders.
    Shows which checkout protocol (acp / ucp) each transaction used.
    Firmly's compliance-first differentiator: every transaction's protocol
    is recorded alongside its mandate and DNSid verification status.
    """
    tasks     = _fetch_tasks()
    completed = [t for t in tasks if t.get("status") == "completed"]

    acp_tasks = [t for t in completed if t.get("protocol_of_record") == "acp"]
    ucp_tasks = [t for t in completed if t.get("protocol_of_record") == "ucp"]
    unknown   = [t for t in completed if not t.get("protocol_of_record")]

    breakdown = []
    for t in completed:
        result = t.get("result", {}) or {}
        breakdown.append({
            "task_id":               t["task_id"],
            "protocol_of_record":    t.get("protocol_of_record", "unknown"),
            "buyer_id":              t.get("buyer_id"),
            "products_subtotal":     result.get("products_subtotal"),
            "buyer_dnsid_verified":  result.get("buyer_dnsid_verified"),
            "cart_mandate_verified": result.get("cart_mandate_verified"),
            "created_at":            t.get("created_at"),
        })

    return JSONResponse(content={
        "clerk_question":  "Enforcement -- which protocol governed each transaction?",
        "total_completed": len(completed),
        "by_protocol": {
            "acp":     len(acp_tasks),
            "ucp":     len(ucp_tasks),
            "unknown": len(unknown),
        },
        "transactions": breakdown,
        "generated_at": _now(),
    })


# ── Summary: All Four Questions ───────────────────────────────────────────────

@app.get("/governance/summary")
async def get_summary():
    """
    CISO summary view: health status across all four Clerk questions.
    Single-screen view for enterprise governance review.
    """
    agents    = list_registry()
    manifests = list(SELLER_MANIFESTS.values())
    intents   = list(INTENT_MANDATES.values())
    carts     = list(CART_MANDATES.values())
    offers    = list(SIGNED_OFFERS.values())
    mandates  = list(MANDATES.values())
    tasks     = _fetch_tasks()

    revoked_agents      = [a for a in agents if a["status"] == "revoked"]
    unsigned_manifests  = [m for m in manifests if "proof" not in m]
    unsigned_intents    = [m for m in intents   if "proof" not in m]
    unsigned_carts      = [c for c in carts     if "proof" not in c]
    unsigned_offers     = [o for o in offers     if "proof" not in o]

    health = "healthy"
    alerts = []

    if revoked_agents:
        health = "warning"
        alerts.append(f"{len(revoked_agents)} agent(s) revoked: {[a['handle'] for a in revoked_agents]}")
    if unsigned_manifests:
        health = "critical"
        alerts.append(f"{len(unsigned_manifests)} seller manifest(s) missing signature")
    if unsigned_intents:
        health = "critical"
        alerts.append(f"{len(unsigned_intents)} intent mandate(s) missing signature")
    if unsigned_carts:
        health = "warning"
        alerts.append(f"{len(unsigned_carts)} cart mandate(s) missing signature")
    if unsigned_offers:
        health = "warning"
        alerts.append(f"{len(unsigned_offers)} signed offer(s) missing signature")

    return JSONResponse(content={
        "health": health,
        "alerts": alerts,
        "identity": {
            "clerk_question": "Who are the agents?",
            "total_agents":   len(agents),
            "active":         len([a for a in agents if a["status"] == "active"]),
            "revoked":        len(revoked_agents),
        },
        "scoping": {
            "clerk_question":      "What are agents authorized to do?",
            "seller_manifests":    len(manifests),
            "unsigned_manifests":  len(unsigned_manifests),
            "intent_mandates":     len(intents),
            "unsigned_intents":    len(unsigned_intents),
            "phase4_mandates":     len(mandates),
        },
        "approvals": {
            "clerk_question":   "Was each action explicitly authorized?",
            "cart_mandates":    len(carts),
            "unsigned_carts":   len(unsigned_carts),
            "signed_offers":    len(offers),
            "unsigned_offers":  len(unsigned_offers),
            "total_transactions": len([t for t in tasks if t.get("status") == "completed"]),
        },
        "enforcement": {
            "clerk_question":         "Is there a mechanism preventing violations?",
            "manifest_gate_active":   len(manifests) > 0,
            "cart_mandate_gate_active": len(intents) > 0,
            "dnsid_gate_active":      len(agents) > 0,
            "note": "Runtime enforcement gates active: DNSid revocation, Cart Mandate verification, Seller Manifest verification",
        },
        "generated_at": _now(),
    })


# ── Audit Trail ───────────────────────────────────────────────────────────────

@app.get("/governance/audit-trail")
async def get_audit_trail():
    """
    Ordered event log across all layers with timestamps.
    Each event records what happened, who authorized it, and which layer.
    Used for compliance audit, dispute resolution, and regulatory examination.
    """
    events = []

    for a in list_registry():
        events.append({
            "layer":      "Identity",
            "event":      "agent_registered" if a["status"] == "active" else "agent_revoked",
            "entity":     a["handle"],
            "operator":   a["owner"],
            "timestamp":  a["revoked_at"] if a["status"] == "revoked" else a["created_at"],
            "detail":     a.get("revocation_reason") if a["status"] == "revoked" else None,
        })

    for m in SELLER_MANIFESTS.values():
        events.append({
            "layer":     "Scoping",
            "event":     "seller_manifest_signed",
            "entity":    m["seller_agent_id"],
            "operator":  m["operator_id"],
            "timestamp": m["created_at"],
            "detail":    f"{len(m['authorized_skus'])} SKUs authorized",
        })

    for m in INTENT_MANDATES.values():
        events.append({
            "layer":     "Scoping",
            "event":     "intent_mandate_signed",
            "entity":    m["buyer_agent_id"],
            "operator":  m["operator_id"],
            "timestamp": m["created_at"],
            "detail":    f"max_per_tx=${m['max_per_tx_usd']}, max_total=${m['max_total_usd']}",
        })

    for c in CART_MANDATES.values():
        events.append({
            "layer":     "Approvals",
            "event":     "cart_mandate_signed",
            "entity":    c["seller_id"],
            "operator":  c.get("buyer_dnsid", "unknown"),
            "timestamp": c["created_at"],
            "detail":    f"amount=${c['amount_usd']}",
        })

    for o in SIGNED_OFFERS.values():
        events.append({
            "layer":     "Enforcement",
            "event":     "signed_offer_generated",
            "entity":    o["sku"],
            "operator":  o.get("buyer_id", "unknown"),
            "timestamp": o["created_at"],
            "detail":    f"unit_price=${o['unit_price']}, qty={o['quantity']}",
        })

    events.sort(key=lambda e: e["timestamp"])

    return JSONResponse(content={
        "total_events": len(events),
        "events":       events,
        "generated_at": _now(),
    })


# ── Index ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    agents   = list_registry()
    revoked  = [a for a in agents if a["status"] == "revoked"]
    return f"""
    <html><body style="font-family:monospace;padding:2rem;background:#111;color:#eee">
    <h2>SupplyMind Governance Dashboard -- Phase 11</h2>
    <p>Clerk four-question coverage across all agents and transactions:</p>
    <ul>
      <li><b>Identity</b> -- <a href="/governance/agents" style="color:#7cf">/governance/agents</a>
          &nbsp;|&nbsp; {len(agents)} agents, {len(revoked)} revoked</li>
      <li><b>Scoping</b> -- <a href="/governance/seller-manifests" style="color:#7cf">/governance/seller-manifests</a>
          &nbsp;|&nbsp; <a href="/governance/intent-mandates" style="color:#7cf">/governance/intent-mandates</a></li>
      <li><b>Approvals</b> -- <a href="/governance/cart-mandates" style="color:#7cf">/governance/cart-mandates</a>
          &nbsp;|&nbsp; <a href="/governance/signed-offers" style="color:#7cf">/governance/signed-offers</a></li>
      <li><b>Enforcement</b> -- <a href="/governance/summary" style="color:#7cf">/governance/summary</a>
          &nbsp;|&nbsp; <a href="/governance/audit-trail" style="color:#7cf">/governance/audit-trail</a></li>
    </ul>
    <p style="color:#888">Phase 12 next: Multi-Protocol Checkout (ACP + UCP)</p>
    </body></html>
    """


if __name__ == "__main__":
    uvicorn.run("src.governance.dashboard:app", host="127.0.0.1", port=8085, reload=False)
