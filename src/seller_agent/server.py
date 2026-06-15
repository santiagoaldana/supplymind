"""
Seller Agent Web Server — Phase 3: The Marketplace

PROTOCOLS IN USE:

1. UCP (Universal Commerce Protocol) — Phase 2, still active
   GET /.well-known/ucp.json     machine-readable product catalog (JSON-LD)

2. KYA (Know Your Agent) — Phase 2, still active
   GET /.well-known/kya.json     seller identity card

3. A2A (Agent-to-Agent) — NEW in Phase 3: The Discovery Layer
   GET  /.well-known/agent-card.json   Seller's A2A business card
   POST /tasks/send                    Buyer sends a purchase order task
   GET  /tasks/{task_id}               Buyer polls task status

   A2A Task Lifecycle:
     submitted  → task received, being processed
     completed  → order confirmed, total calculated
     failed     → stock unavailable or validation error

4. x402 (HTTP 402 Payment Required) — NEW in Phase 3: The Micro-Settlement Layer
   GET /quotes/{sku}
     If order value <= $500: returns quote immediately (free)
     If order value >  $500: returns HTTP 402 with USDC payment instructions
     After simulated payment: returns full quote

   x402 Wire Flow:
     Buyer  → GET /quotes/PPR-001?quantity=100
     Seller → 402 Payment Required
               {"amount": "0.10", "currency": "USDC", "payTo": "0x..."}
     Buyer  → GET /quotes/PPR-001?quantity=100  (with X-Payment header)
     Seller → 200 OK  {"unit_price": 44.99, "bulk_discount": "2.2%", ...}

Run:
  .venv/bin/python src/seller_agent/server.py
"""

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

from src.inventory_server.db import init_db, get_connection
from src.seller_agent.generate_ucp import generate_ucp_catalog
from src.seller_agent.ucp_profile import generate_ucp_profile
from src.identity.dnsid import resolve_dnsid
from src.identity.dnsid_registry_seed import seed as seed_dnsid_registry
from src.identity.signed_mandate import verify_cart_mandate
from src.identity.visa_tap import verify_tap_credential, credential_from_header
from src.identity.mastercard_agent_pay import verify_agentic_token, AGENTIC_TOKENS
from src.identity.seller_manifest import (
    create_seller_manifest,
    create_signed_offer,
    SELLER_MANIFESTS,
)
from src.identity.keys import load_or_create_private_key_from_file
from src.seller_agent.protocol_router import normalize_acp, normalize_ucp_task, NormalizedOrder
from src.governance.event_log import log_event
from src.payment_server.wallet import execute_payment, get_wallets_by_owner, list_wallets
from src.payment_server.wallet_seed import seed as seed_wallets
from src.fraud.rate_limiter import check_rate_limit
from src.fraud.sardine_client import score_transaction

# CLI args: --port, --well-known-dir, --name
# Defaults match Phase 3 behavior so all existing tests still work.
_parser = argparse.ArgumentParser(add_help=False)
_parser.add_argument("--port",             type=int,  default=8080)
_parser.add_argument("--well-known-dir",   type=str,  default=None)
_parser.add_argument("--name",             type=str,  default="SupplyMind Seller Agent")
_parser.add_argument("--price-multiplier", type=float, default=1.0)
_parser.add_argument("--dnsid-handle",     type=str,  default=None)
_args, _ = _parser.parse_known_args()

SERVER_PORT   = _args.port
SERVER_NAME   = _args.name
PRICE_MULT    = _args.price_multiplier
DNSID_HANDLE  = _args.dnsid_handle

_default_well_known = Path(__file__).parent / "well_known"
WELL_KNOWN      = Path(_args.well_known_dir) if _args.well_known_dir else _default_well_known
KYA_PATH        = WELL_KNOWN / "kya.json"
AGENT_CARD_PATH = WELL_KNOWN / "agent-card.json"

init_db()
seed_dnsid_registry()
seed_wallets()

# Load or create the seller agent's signing key (reuses Phase 7 key file pattern)
_SELLER_KEY_FILE = Path(__file__).parent.parent.parent / "data" / "seller_agent.key.hex"
_SELLER_PRIVATE_KEY = load_or_create_private_key_from_file(_SELLER_KEY_FILE)

# Seed the Seller Authorization Manifest at startup.
# In production this is created once by the merchant operator via LoginID ceremony.
_SELLER_MANIFEST = create_seller_manifest(
    operator_id     = "ops@supplymind.localhost",
    seller_agent_id = "did:web:localhost:8080",
    seller_dnsid    = "dnsid://supplymind.localhost/agents/seller-001",
    authorized_skus = [
        {"sku": "PPR-001", "min_price_usd":  5.00, "max_price_usd":  30.00, "max_discount_pct": 5.0},
        {"sku": "PPR-002", "min_price_usd":  5.00, "max_price_usd":  30.00, "max_discount_pct": 5.0},
        {"sku": "PEN-001", "min_price_usd":  1.00, "max_price_usd":  20.00, "max_discount_pct": 3.0},
        {"sku": "STK-001", "min_price_usd":  1.00, "max_price_usd":  20.00, "max_discount_pct": 3.0},
    ],
    private_key     = _SELLER_PRIVATE_KEY,
)

app = FastAPI(
    title="SupplyMind Seller Agent",
    description="Phase 3: UCP + KYA + A2A task lifecycle + x402 micro-payment",
    version="3.0.0",
)

# In-memory task store. Phase 5 will persist this to SQLite.
TASKS: dict[str, dict] = {}

# Simulated x402 payment receipts (token -> paid status)
PAID_QUOTES: set[str] = set()

X402_QUOTE_FEE_USD            = 0.10
X402_THRESHOLD_USD            = 500.00
X402_THRESHOLD_VERIFIED_USD   = 1000.00
SELLER_WALLET                 = "0xSUPPLYMIND_SELLER_WALLET_PLACEHOLDER"


# ── Well-known endpoints (Phase 2, still active) ──────────────────────────────

@app.get("/.well-known/ucp.json")
async def get_ucp_catalog():
    """UCP: machine-readable product catalog (JSON-LD)."""
    return JSONResponse(
        content=generate_ucp_catalog(base_url=f"http://localhost:{SERVER_PORT}", price_multiplier=PRICE_MULT),
        media_type="application/ld+json",
    )


@app.get("/.well-known/kya.json")
async def get_kya_identity():
    """KYA: seller agent identity card."""
    return JSONResponse(content=json.loads(KYA_PATH.read_text()), media_type="application/ld+json")


@app.get("/.well-known/agent-card.json")
async def get_agent_card():
    """
    A2A Protocol: Agent Card endpoint.
    The Buyer Agent fetches this first to discover what the Seller can do
    and where to send purchase tasks. This is the A2A equivalent of a
    business card — name, capabilities, and task endpoint URL.
    """
    return JSONResponse(content=json.loads(AGENT_CARD_PATH.read_text()), media_type="application/json")


# ── Seller Authorization Manifest (Phase 10) ─────────────────────────────────

@app.get("/.well-known/seller-manifest.json")
async def get_seller_manifest():
    """
    Phase 10: Seller Authorization Manifest endpoint.
    Buyer agents and chat interfaces fetch this to verify the seller's
    signed authorization before presenting any offer to the human buyer.
    Equivalent of HTTPS certificate -- machine-readable, cryptographically signed.
    """
    return JSONResponse(content=_SELLER_MANIFEST, media_type="application/json")


# ── A2A Task Models ───────────────────────────────────────────────────────────

class OrderLine(BaseModel):
    sku: str
    quantity: int

class PurchaseTaskRequest(BaseModel):
    """
    A2A Protocol: the task payload the Buyer Agent sends to POST /tasks/send.
    Each task has a buyer_id (who is sending), a list of order lines,
    shipping details, and optional notes.

    cart_mandate: optional AP2 v0.2.0 signed Cart Mandate dict (Phase 9).
      If present, the seller verifies the full chain: agent signature on the
      Cart Mandate + human operator signature on the linked Intent Mandate.
      If verification fails, the purchase is rejected with 403.
      If absent, purchase proceeds under Phase 4 unsigned mandate policy.
    """
    buyer_id:        str
    order_lines:     list[OrderLine]
    origin_zip:      str
    destination_zip: str
    service_level:   str = "standard"
    notes:           Optional[str] = None
    cart_mandate:    Optional[dict] = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _process_order(order_lines: list[OrderLine]) -> tuple[list[dict], float, list[str]]:
    """
    Validate stock and calculate line item totals.
    Returns (line_items, subtotal, errors).
    """
    conn = get_connection()
    line_items = []
    subtotal   = 0.0
    errors     = []

    for line in order_lines:
        row = conn.execute(
            "SELECT * FROM products WHERE sku = ?", (line.sku.upper(),)
        ).fetchone()

        if not row:
            errors.append(f"SKU {line.sku} not found")
            continue

        if row["stock_qty"] < line.quantity:
            errors.append(
                f"SKU {line.sku}: requested {line.quantity}, "
                f"only {row['stock_qty']} in stock"
            )
            continue

        item_total = round(row["unit_price"] * line.quantity, 2)
        subtotal  += item_total
        line_items.append({
            "sku":            row["sku"],
            "name":           row["name"],
            "quantity":       line.quantity,
            "unit_price":     row["unit_price"],
            "unit_of_measure":row["unit_of_measure"],
            "item_total":     item_total,
            "wallet_address": row["wallet_address"],
        })

    conn.close()
    return line_items, round(subtotal, 2), errors


# ── Shared order execution (Phase 12: protocol router feeds this) ─────────────

def _apply_gates(
    order: NormalizedOrder,
    tap_header: Optional[str] = None,
    mc_token_id: Optional[str] = None,
    client_ip: str = "unknown",
) -> tuple[bool, bool, Optional[str], bool, bool]:
    """
    Apply fraud, DNSid, Cart Mandate, Visa TAP, and Mastercard Agent Pay gates.
    Returns (buyer_dnsid_verified, cart_mandate_verified, operator_id,
             tap_verified, mc_token_verified).
    Raises HTTPException 403 on gate failure.
    Security invariant: all gates run before any order processing.
    """
    # Phase 15: rate limit gate (DNSid-anchored)
    rate_result = check_rate_limit(order.buyer_dnsid, client_ip=client_ip)
    if not rate_result.allowed:
        log_event("Enforcement", "rate_limit_blocked", order.buyer_id, "fraud",
                  f"identity={rate_result.identity} reason={rate_result.reason}")
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded: {rate_result.reason}")

    # Phase 15: Sardine fraud scoring gate
    order_value = sum(
        l.get("quantity", 1) * l.get("unit_price", 0.0)
        for l in order.order_lines
    ) if order.order_lines and isinstance(order.order_lines[0], dict) else 0.0
    total_quantity = sum(
        l.get("quantity", 1) for l in order.order_lines
    ) if order.order_lines and isinstance(order.order_lines[0], dict) else 1

    dnsid_status = "unknown"
    if order.buyer_dnsid:
        dnsid_record = resolve_dnsid(order.buyer_dnsid)
        dnsid_status = dnsid_record.get("status", "unknown")

    sardine = score_transaction(
        agent_dnsid=order.buyer_dnsid,
        dnsid_status=dnsid_status,
        order_value_usd=order_value,
        quantity=total_quantity,
        request_count_per_minute=rate_result.request_count,
        buyer_id=order.buyer_id,
        client_ip=client_ip,
    )
    log_event("Enforcement", "fraud_score", order.buyer_id, "sardine",
              f"score={sardine.score} level={sardine.level} decision={sardine.decision} "
              f"mock={sardine.mock} signals={sardine.signals}")
    if sardine.decision == "block":
        raise HTTPException(
            status_code=403,
            detail=f"Transaction blocked by fraud detection: score={sardine.score} signals={sardine.signals}",
        )

    buyer_dnsid_verified = False
    if order.buyer_dnsid:
        dnsid_record = resolve_dnsid(order.buyer_dnsid)
        if dnsid_record.get("status") == "revoked":
            raise HTTPException(
                status_code=403,
                detail=f"Buyer DNSid {order.buyer_dnsid} is revoked. Purchase rejected.",
            )
        buyer_dnsid_verified = dnsid_record.get("status") == "active"

    cart_mandate_verified = False
    operator_id           = None
    if order.cart_mandate:
        verification = verify_cart_mandate(order.cart_mandate)
        if verification["decision"] == "reject":
            raise HTTPException(
                status_code=403,
                detail=f"Cart Mandate verification failed: {verification['reason']}",
            )
        cart_mandate_verified = True
        operator_id           = verification.get("operator_id")

    # Visa TAP gate (optional -- present = verified, absent = not verified)
    tap_verified = False
    if tap_header:
        try:
            credential = credential_from_header(tap_header)
            valid, reason = verify_tap_credential(credential)
            if not valid:
                raise HTTPException(status_code=403, detail=f"Visa TAP credential invalid: {reason}")
            tap_verified = True
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=403, detail=f"Visa TAP header malformed: {e}")

    # Mastercard Agent Pay gate (optional -- present = verified, absent = not verified)
    mc_token_verified = False
    if mc_token_id:
        token = AGENTIC_TOKENS.get(mc_token_id)
        if not token:
            raise HTTPException(status_code=403, detail=f"MC Agentic Token {mc_token_id} not found")
        subtotal = sum(i.get("quantity", 1) for i in order.order_lines) * 10.0  # conservative estimate
        valid, reason = verify_agentic_token(token, "did:web:localhost:8080", subtotal)
        if not valid:
            raise HTTPException(status_code=403, detail=f"MC Agentic Token invalid: {reason}")
        mc_token_verified = True

    return buyer_dnsid_verified, cart_mandate_verified, operator_id, tap_verified, mc_token_verified


def _build_task_result(
    order: NormalizedOrder,
    tap_header: Optional[str] = None,
    mc_token_id: Optional[str] = None,
    client_ip: str = "unknown",
) -> JSONResponse:
    """
    Execute an order from any protocol and return a task result.
    Called by both UCP (/tasks/send) and ACP (/acp/v1/checkout) endpoints.
    """
    buyer_dnsid_verified, cart_mandate_verified, operator_id, tap_verified, mc_token_verified = \
        _apply_gates(order, tap_header=tap_header, mc_token_id=mc_token_id, client_ip=client_ip)

    task_id    = str(uuid.uuid4())
    created_at = _now()

    task: dict = {
        "task_id":           task_id,
        "status":            "submitted",
        "created_at":        created_at,
        "updated_at":        created_at,
        "buyer_id":          order.buyer_id,
        "protocol_of_record": order.protocol,
        "request":           order.raw_payload,
    }
    TASKS[task_id] = task

    raw_lines = [OrderLine(sku=l["sku"], quantity=l["quantity"]) for l in order.order_lines]
    line_items, subtotal, errors = _process_order(raw_lines)

    if errors:
        task["status"]     = "failed"
        task["updated_at"] = _now()
        task["errors"]     = errors
        task["result"]     = None
        return JSONResponse(content=task, status_code=422)

    task["status"]     = "completed"
    task["updated_at"] = _now()
    task["errors"]     = []
    # Phase 13a: execute wallet payment
    buyer_wallets  = get_wallets_by_owner(order.buyer_id)
    seller_wallets = get_wallets_by_owner("did:web:localhost:8080")
    payment_result = None

    # Prefer USDC wallet; fall back to fiat
    buyer_wallet  = next((w for w in buyer_wallets  if w["wallet_type"] == "coinbase_usdc"), None) or \
                    next((w for w in buyer_wallets   if w["wallet_type"] == "stripe_link"),    None)
    seller_wallet = next((w for w in seller_wallets if w["wallet_type"] == "coinbase_usdc"), None)

    if buyer_wallet and seller_wallet:
        payment_result = execute_payment(
            from_wallet_id = buyer_wallet["wallet_id"],
            to_wallet_id   = seller_wallet["wallet_id"],
            amount         = subtotal,
            task_id        = task_id,
        )
        if payment_result.get("status") == "insufficient_funds":
            task["status"]     = "failed"
            task["updated_at"] = _now()
            task["errors"]     = [f"Payment failed: {payment_result['reason']}"]
            task["result"]     = None
            TASKS[task_id]     = task
            return JSONResponse(content=task, status_code=402)

    task["result"] = {
        "line_items":        line_items,
        "products_subtotal": subtotal,
        "shipping": {
            "origin_zip":      order.origin_zip,
            "destination_zip": order.destination_zip,
            "service_level":   order.service_level,
            "note":            "Shipping cost calculated by MCP Shipping Server at order execution time",
        },
        "payment_result":        payment_result,
        "buyer_dnsid_verified":  buyer_dnsid_verified,
        "cart_mandate_verified": cart_mandate_verified,
        "operator_id":           operator_id,
        "tap_verified":          tap_verified,
        "mc_token_verified":     mc_token_verified,
        "protocol_of_record":    order.protocol,
    }

    TASKS[task_id] = task
    log_event("Enforcement", "transaction_completed", order.buyer_id,
              order.protocol,
              f"task_id={task_id} subtotal=${subtotal} protocol={order.protocol} "
              f"dnsid={buyer_dnsid_verified} mandate={cart_mandate_verified} "
              f"tap={tap_verified} mc={mc_token_verified}")
    return JSONResponse(content=task, status_code=201)


# ── A2A / UCP Task Endpoint ───────────────────────────────────────────────────

@app.post("/tasks/send", status_code=201)
async def send_task(
    request: Request,
    task_req: PurchaseTaskRequest,
    x_agent_dnsid:    Optional[str] = Header(default=None, alias="X-Agent-DNSid"),
    tap_credential:   Optional[str] = Header(default=None, alias="TAP-Agent-Credential"),
    mc_token_id:      Optional[str] = Header(default=None, alias="MC-Agent-Token-Id"),
):
    """
    A2A + UCP Protocol: receive a purchase task from a Buyer Agent.
    Phase 14: Visa TAP (TAP-Agent-Credential) and MC Agent Pay (MC-Agent-Token-Id)
    headers accepted and verified alongside existing DNSid and Cart Mandate gates.
    Phase 15: Sardine fraud scoring and DNSid rate limiting applied before all other gates.
    """
    client_ip = request.client.host if request.client else "unknown"
    order = normalize_ucp_task(task_req.model_dump(), buyer_dnsid=x_agent_dnsid)
    return _build_task_result(order, tap_header=tap_credential, mc_token_id=mc_token_id, client_ip=client_ip)


# ── ACP Checkout Endpoint (Phase 12) ─────────────────────────────────────────

class AcpItem(BaseModel):
    product_id: str
    quantity:   int

class AcpShipping(BaseModel):
    origin:      str = "00000"
    destination: str = "00000"
    service:     str = "standard"

class AcpCheckoutRequest(BaseModel):
    """
    ACP (OpenAI/Stripe Agentic Commerce Protocol) checkout request.
    A buyer agent built on GPT-4o sends this format instead of A2A /tasks/send.
    The protocol router normalizes it to the same internal format before processing.
    """
    buyer_id:       str
    items:          list[AcpItem]
    shipping:       AcpShipping = AcpShipping()
    payment_intent: Optional[str] = None
    cart_mandate:   Optional[dict] = None


@app.post("/acp/v1/checkout", status_code=201)
async def acp_checkout(
    request: Request,
    req: AcpCheckoutRequest,
    x_agent_dnsid:  Optional[str] = Header(default=None, alias="X-Agent-DNSid"),
    tap_credential: Optional[str] = Header(default=None, alias="TAP-Agent-Credential"),
    mc_token_id:    Optional[str] = Header(default=None, alias="MC-Agent-Token-Id"),
):
    """
    ACP Protocol: Agentic Commerce Protocol checkout endpoint.
    Phase 14: Visa TAP and MC Agent Pay gates applied alongside DNSid/Cart Mandate.
    Phase 15: Sardine fraud scoring and DNSid rate limiting applied before all other gates.
    """
    client_ip = request.client.host if request.client else "unknown"
    payload = req.model_dump()
    order   = normalize_acp(payload, buyer_dnsid=x_agent_dnsid)
    return _build_task_result(order, tap_header=tap_credential, mc_token_id=mc_token_id, client_ip=client_ip)


@app.get("/tasks")
async def list_tasks():
    """List all tasks -- used by governance dashboard for protocol-of-record audit."""
    return JSONResponse(content=list(TASKS.values()))


@app.get("/governance/data/agents")
async def governance_agents():
    """Governance: export DNSid registry for dashboard cross-process read."""
    from src.identity.dnsid import list_registry
    return JSONResponse(content=list_registry())


@app.get("/governance/data/manifests")
async def governance_manifests():
    """Governance: export seller manifests for dashboard cross-process read."""
    return JSONResponse(content=list(SELLER_MANIFESTS.values()))


@app.get("/governance/data/intent-mandates")
async def governance_intent_mandates():
    """Governance: export intent mandates for dashboard cross-process read."""
    from src.identity.signed_mandate import INTENT_MANDATES
    return JSONResponse(content=list(INTENT_MANDATES.values()))


@app.get("/governance/data/cart-mandates")
async def governance_cart_mandates():
    """Governance: export cart mandates for dashboard cross-process read."""
    from src.identity.signed_mandate import CART_MANDATES
    return JSONResponse(content=list(CART_MANDATES.values()))


@app.get("/governance/data/signed-offers")
async def governance_signed_offers():
    """Governance: export signed offers for dashboard cross-process read."""
    from src.identity.seller_manifest import SIGNED_OFFERS
    return JSONResponse(content=list(SIGNED_OFFERS.values()))


@app.get("/governance/data/wallets")
async def governance_wallets():
    """Governance: export all wallet states for dashboard cross-process read."""
    return JSONResponse(content=list_wallets())


@app.get("/wallet/balance")
async def wallet_balance(owner_id: str = "did:web:localhost:8090"):
    """Return current wallet balances for an owner. Used by demo script."""
    wallets = get_wallets_by_owner(owner_id)
    return JSONResponse(content={
        "owner_id": owner_id,
        "wallets":  wallets,
    })


@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """
    A2A Protocol: poll task status by task_id.
    The Buyer Agent calls this after POST /tasks/send to check
    whether the order was confirmed or failed.
    """
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return JSONResponse(content=task)


# ── x402 Quote Endpoint ───────────────────────────────────────────────────────

@app.get("/quotes/{sku}")
async def get_quote(
    sku: str,
    quantity: int = 1,
    x_payment:     Optional[str] = Header(default=None, alias="X-Payment"),
    x_agent_dnsid: Optional[str] = Header(default=None, alias="X-Agent-DNSid"),
):
    """
    x402 Protocol: return a bulk quote for a SKU.

    x402 Wire Flow:
      1. Buyer calls GET /quotes/{sku}?quantity=100
      2. If order value > $500 AND no X-Payment header:
            Server returns HTTP 402 Payment Required
            Body contains amount, currency, and payTo wallet address
      3. Buyer simulates payment and retries with X-Payment header
      4. Server returns full quote with bulk discount

    This implements the 'tollbooth' model: premium data costs a micro-fee.
    In production the X-Payment header contains a signed USDC transaction hash.
    In Phase 3 any non-empty X-Payment header is accepted as proof of payment.
    Phase 4 verifies the actual on-chain transaction via Circle API.
    """
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM products WHERE sku = ?", (sku.upper(),)
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"SKU {sku} not found")

    order_value = round(row["unit_price"] * quantity, 2)

    buyer_dnsid_verified = False
    if x_agent_dnsid:
        dnsid_record = resolve_dnsid(x_agent_dnsid)
        if dnsid_record.get("status") == "revoked":
            raise HTTPException(
                status_code=403,
                detail=f"Buyer DNSid {x_agent_dnsid} is revoked. Quote rejected.",
            )
        buyer_dnsid_verified = dnsid_record.get("status") == "active"

    effective_threshold = X402_THRESHOLD_VERIFIED_USD if buyer_dnsid_verified else X402_THRESHOLD_USD

    if order_value > effective_threshold and not x_payment:
        # x402: return 402 Payment Required
        # The response body follows the x402 specification:
        # amount, currency, payTo address, and a description of what the payment unlocks.
        threshold_hint = (
            f"${X402_THRESHOLD_VERIFIED_USD:.0f} for DNSid-verified buyers"
            if not buyer_dnsid_verified
            else f"${X402_THRESHOLD_VERIFIED_USD:.0f} (you are DNSid-verified)"
        )
        payment_challenge = {
            "x402_version":        "1",
            "error":               "Payment required to access bulk quote",
            "amount":              str(X402_QUOTE_FEE_USD),
            "currency":            "USDC",
            "network":             "Ethereum Sepolia testnet",
            "payTo":               SELLER_WALLET,
            "free_quote_threshold": threshold_hint,
            "description": (
                f"Pay {X402_QUOTE_FEE_USD} USDC to {SELLER_WALLET} to receive "
                f"the bulk quote for {quantity}x {row['name']}. "
                f"Retry this request with the transaction hash in the X-Payment header. "
                f"Tip: present a valid X-Agent-DNSid header to raise the free-quote threshold to "
                f"${X402_THRESHOLD_VERIFIED_USD:.0f}."
            ),
            "retry_url": f"http://localhost:{SERVER_PORT}/quotes/{sku}?quantity={quantity}",
        }
        return JSONResponse(content=payment_challenge, status_code=402)

    bulk_discount_pct = 0.0
    if quantity >= 100:
        bulk_discount_pct = 5.0
    elif quantity >= 50:
        bulk_discount_pct = 3.0
    elif quantity >= 20:
        bulk_discount_pct = 2.0

    discounted_price = round(row["unit_price"] * (1 - bulk_discount_pct / 100), 4)
    discounted_total = round(discounted_price * quantity, 2)

    signed_offer = create_signed_offer(
        manifest_id  = _SELLER_MANIFEST["manifest_id"],
        sku          = sku,
        quantity     = quantity,
        unit_price   = row["unit_price"],
        discount_pct = bulk_discount_pct,
        private_key  = _SELLER_PRIVATE_KEY,
    )
    # Embed the manifest so the buyer can verify the full chain without a separate fetch.
    if "error" not in signed_offer:
        signed_offer["seller_manifest"] = _SELLER_MANIFEST

    quote = {
        "sku":                sku.upper(),
        "name":               row["name"],
        "quantity":           quantity,
        "standard_unit_price":row["unit_price"],
        "bulk_discount_pct":  bulk_discount_pct,
        "quoted_unit_price":  discounted_price,
        "quoted_total":       discounted_total,
        "stock_available":    row["stock_qty"],
        "currency":           "USD",
        "wallet_address":     row["wallet_address"],
        "quote_valid_until":  "2026-05-12T00:00:00Z",
        "x402_paid":              x_payment is not None,
        "buyer_dnsid_verified":   buyer_dnsid_verified,
        "signed_offer":           signed_offer if "error" not in signed_offer else None,
        "payment_note":           (
            "Phase 4: AP2 Mandate will authorize USDC settlement to wallet_address above."
        ),
    }
    return JSONResponse(content=quote)


# ── Google UCP v2026-04-08 Endpoints ─────────────────────────────────────────

# In-memory checkout session store (parallel to TASKS, same pattern)
CHECKOUT_SESSIONS: dict[str, dict] = {}


@app.get("/.well-known/ucp")
async def get_ucp_profile():
    """
    Google UCP Protocol: serve the UCP Profile document.
    This is the entry point for any Google UCP-compliant buyer agent.
    It declares capabilities and payment handlers — not a product list.
    Contrast with /.well-known/ucp.json (our Phase 2 catalog convention).
    """
    base_url = f"http://localhost:{SERVER_PORT}"
    return JSONResponse(
        content=generate_ucp_profile(base_url=base_url, seller_name=SERVER_NAME),
        media_type="application/json",
    )


class UcpLineItem(BaseModel):
    sku:      str
    quantity: int

class CheckoutSessionRequest(BaseModel):
    """Google UCP: buyer sends line items to open a checkout session."""
    line_items: list[UcpLineItem]
    buyer_id:   Optional[str] = None

class CheckoutCompleteRequest(BaseModel):
    """Google UCP: buyer submits payment token to confirm the order."""
    payment_token: str
    buyer_id:      Optional[str] = None


@app.post("/ucp/v1/checkout-sessions", status_code=201)
async def create_checkout_session(req: CheckoutSessionRequest):
    """
    Google UCP: create a checkout session with the buyer's line items.
    Returns session_id, line item details, subtotal, and payment handler config.
    The session status starts as 'incomplete' until complete is called.
    Reuses _process_order() for stock validation and pricing.
    """
    session_id = str(uuid.uuid4())
    created_at = _now()

    order_lines = [OrderLine(sku=li.sku, quantity=li.quantity) for li in req.line_items]
    line_items, subtotal, errors = _process_order(order_lines)

    if errors:
        return JSONResponse(
            content={"error": "order_validation_failed", "details": errors},
            status_code=422,
        )

    session = {
        "session_id":      session_id,
        "status":          "incomplete",
        "buyer_id":        req.buyer_id,
        "line_items":      line_items,
        "subtotal_usd":    subtotal,
        "payment_handler": "stripe_test",
        "created_at":      created_at,
        "updated_at":      created_at,
    }
    CHECKOUT_SESSIONS[session_id] = session
    return JSONResponse(content=session, status_code=201)


@app.patch("/ucp/v1/checkout-sessions/{session_id}")
async def update_checkout_session(session_id: str, req: CheckoutSessionRequest):
    """
    Google UCP: update an existing checkout session (add/remove items).
    Recalculates totals with the new line items.
    """
    session = CHECKOUT_SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    if session["status"] != "incomplete":
        raise HTTPException(status_code=409, detail="Session already completed")

    order_lines = [OrderLine(sku=li.sku, quantity=li.quantity) for li in req.line_items]
    line_items, subtotal, errors = _process_order(order_lines)

    if errors:
        return JSONResponse(
            content={"error": "order_validation_failed", "details": errors},
            status_code=422,
        )

    session["line_items"]   = line_items
    session["subtotal_usd"] = subtotal
    session["updated_at"]   = _now()
    return JSONResponse(content=session)


@app.post("/ucp/v1/checkout-sessions/{session_id}/complete", status_code=201)
async def complete_checkout_session(session_id: str, req: CheckoutCompleteRequest):
    """
    Google UCP: submit payment token and confirm the order.
    In Phase 5C the payment token is any non-empty string (simulated).
    Phase 8 will verify a real Stripe SPT or Circle USDC transaction hash.
    Creates an order record in TASKS (reuses existing task structure).
    Returns order_id + status: completed.
    """
    session = CHECKOUT_SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    if session["status"] != "incomplete":
        raise HTTPException(status_code=409, detail="Session already completed")
    if not req.payment_token:
        raise HTTPException(status_code=400, detail="payment_token is required")

    order_id   = str(uuid.uuid4())
    completed_at = _now()

    order = {
        "task_id":    order_id,
        "order_id":   order_id,
        "status":     "completed",
        "created_at": session["created_at"],
        "updated_at": completed_at,
        "buyer_id":   req.buyer_id or session.get("buyer_id"),
        "protocol":   "google-ucp-v2026-04-08",
        "request":    {"session_id": session_id, "payment_token": req.payment_token},
        "errors":     [],
        "result": {
            "line_items":        session["line_items"],
            "products_subtotal": session["subtotal_usd"],
            "payment_token":     req.payment_token,
            "payment_note":      "Payment token accepted. Phase 8: verify real Stripe SPT or Circle tx.",
        },
    }
    TASKS[order_id] = order

    session["status"]   = "completed"
    session["order_id"] = order_id
    session["updated_at"] = completed_at

    return JSONResponse(content={"order_id": order_id, "status": "completed"}, status_code=201)


@app.get("/ucp/v1/orders/{order_id}")
async def get_ucp_order(order_id: str):
    """
    Google UCP: retrieve order status by order_id.
    Orders created via UCP checkout-sessions/complete are stored in TASKS.
    """
    order = TASKS.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return JSONResponse(content=order)


# ── Universal Cart (Phase 12.5) ───────────────────────────────────────────────

from src.cart_server.cart import create_cart, add_item, remove_item, get_cart, checkout_cart as _checkout_cart
from src.governance.event_log import log_event as _log_cart_event


@app.post("/cart/v1/carts", status_code=201)
async def cart_create(request: Request):
    body = await request.json()
    buyer_did = body.get("buyer_did", "unknown")
    cart = create_cart(buyer_did)
    _log_cart_event("Scoping", "cart_created", cart["cart_id"], buyer_did,
                    f"cart created via HTTP for buyer_did={buyer_did}")
    return JSONResponse(content=cart, status_code=201)


@app.get("/cart/v1/carts/{cart_id}")
async def cart_get(cart_id: str):
    try:
        return JSONResponse(content=get_cart(cart_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.patch("/cart/v1/carts/{cart_id}")
async def cart_update(cart_id: str, request: Request):
    body = await request.json()
    action = body.get("action")
    try:
        if action == "add":
            cart = add_item(
                cart_id,
                product_id=body["product_id"],
                quantity=int(body["quantity"]),
                unit_price=float(body["unit_price"]),
                seller_did=body.get("seller_did", "unknown"),
                seller_endpoint=body.get("seller_endpoint", ""),
            )
            _log_cart_event("Scoping", "cart_item_added", cart_id,
                            body.get("seller_did", "unknown"),
                            f"product={body['product_id']} qty={body['quantity']} added")
        elif action == "remove":
            cart = remove_item(cart_id, body["item_id"])
        else:
            raise HTTPException(status_code=400, detail="action must be 'add' or 'remove'")
        return JSONResponse(content=cart)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/cart/v1/carts/{cart_id}/checkout", status_code=200)
async def cart_checkout(cart_id: str, request: Request):
    body = await request.json()
    buyer_did = body.get("buyer_did", "")
    try:
        result = _checkout_cart(cart_id, buyer_did)
        _log_cart_event("Approvals", "cart_checked_out", cart_id, buyer_did,
                        f"cart {cart_id} checked out, total={result['total_usd']} USD")
        return JSONResponse(content=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Index ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    task_count = len(TASKS)
    return f"""
    <html><body style="font-family:monospace;padding:2rem;background:#111;color:#eee">
    <h2>SupplyMind Seller Agent — Phase 3</h2>
    <p>Active protocols:</p>
    <ul>
      <li><b>UCP</b> — <a href="/.well-known/ucp.json" style="color:#7cf">/.well-known/ucp.json</a></li>
      <li><b>KYA</b> — <a href="/.well-known/kya.json" style="color:#7cf">/.well-known/kya.json</a></li>
      <li><b>A2A Agent Card</b> — <a href="/.well-known/agent-card.json" style="color:#7cf">/.well-known/agent-card.json</a></li>
      <li><b>A2A Tasks</b> — POST /tasks/send &nbsp;|&nbsp; GET /tasks/{{id}} &nbsp;|&nbsp; Tasks in memory: {task_count}</li>
      <li><b>x402 Quotes</b> — <a href="/quotes/PPR-001?quantity=10" style="color:#7cf">GET /quotes/PPR-001?quantity=10</a> (free)
          &nbsp;|&nbsp; <a href="/quotes/PPR-001?quantity=200" style="color:#f97">GET /quotes/PPR-001?quantity=200</a> (402)</li>
    </ul>
    <p style="color:#888">Phase 4 next: AP2 Mandate + MPP Session + real USDC settlement</p>
    </body></html>
    """


if __name__ == "__main__":
    uvicorn.run("src.seller_agent.server:app", host="127.0.0.1", port=SERVER_PORT, reload=False)
