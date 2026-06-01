"""
Protocol Router -- Phase 12: Multi-Protocol Checkout

Normalizes ACP (OpenAI/Stripe) and UCP (Google/Walmart) checkout requests
into a common internal OrderRequest format before passing to the order
processing pipeline.

WHY A ROUTER:
  UCP buyers (Gemini, Google Shopping agents) and ACP buyers (GPT-4o, Stripe
  Checkout agents) speak different wire formats. Without a router, the seller
  must implement two separate pipelines, doubling the surface area for bugs
  and security gaps. With a router, the shared pipeline (stock check, pricing,
  DNSid gate, Cart Mandate verification, Seller Manifest signing) runs once
  regardless of which protocol the buyer spoke.

SECURITY INVARIANT (from protocol_reflection.md):
  Identity checks (DNSid gate) and authorization checks (Cart Mandate, Seller
  Manifest) are applied BEFORE routing, not after. A buyer arriving via ACP
  is subject to the same gates as a buyer arriving via UCP. The protocol is
  a transport choice, not a trust level.

PROTOCOL-OF-RECORD:
  Every order result carries a protocol_of_record field: "acp" or "ucp".
  This feeds the governance audit trail so the CISO can see which protocol
  each transaction used -- Firmly's compliance-first differentiation.

ACP WIRE FORMAT (simplified, based on OpenAI/Stripe ACP spec):
  POST /acp/v1/checkout
  {
    "buyer_id": str,
    "items": [{"product_id": str, "quantity": int}],
    "shipping": {"origin": str, "destination": str, "service": str},
    "payment_intent": str  -- Stripe payment intent ID (simulated)
  }

UCP WIRE FORMAT (existing, Phase 2+):
  POST /tasks/send  (A2A task envelope)
  POST /ucp/v1/checkout-sessions  (Google UCP)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class NormalizedOrder:
    """Common internal representation for any checkout protocol."""
    buyer_id:        str
    order_lines:     list[dict]          # [{"sku": str, "quantity": int}]
    origin_zip:      str
    destination_zip: str
    service_level:   str
    protocol:        str                  # "acp" or "ucp"
    raw_payload:     dict                 # original request for audit trail
    cart_mandate:    Optional[dict] = None
    buyer_dnsid:     Optional[str]  = None
    payment_ref:     Optional[str]  = None  # Stripe payment intent (ACP) or x402 token (UCP)


def normalize_acp(payload: dict, buyer_dnsid: Optional[str] = None) -> NormalizedOrder:
    """
    Normalize an ACP checkout request to NormalizedOrder.

    ACP uses "items" with "product_id" (maps to SKU) and "quantity".
    Shipping is a nested object with origin/destination/service fields.
    """
    items = payload.get("items", [])
    order_lines = [
        {"sku": item.get("product_id", ""), "quantity": item.get("quantity", 1)}
        for item in items
    ]

    shipping = payload.get("shipping", {})

    return NormalizedOrder(
        buyer_id        = payload.get("buyer_id", "unknown"),
        order_lines     = order_lines,
        origin_zip      = shipping.get("origin", "00000"),
        destination_zip = shipping.get("destination", "00000"),
        service_level   = shipping.get("service", "standard"),
        protocol        = "acp",
        raw_payload     = payload,
        cart_mandate    = payload.get("cart_mandate"),
        buyer_dnsid     = buyer_dnsid,
        payment_ref     = payload.get("payment_intent"),
    )


def normalize_ucp_task(payload: dict, buyer_dnsid: Optional[str] = None) -> NormalizedOrder:
    """
    Normalize an A2A/UCP task request (POST /tasks/send) to NormalizedOrder.
    This is the existing Phase 3+ wire format, wrapped for router compatibility.
    """
    order_lines = [
        {"sku": line.get("sku", ""), "quantity": line.get("quantity", 1)}
        for line in payload.get("order_lines", [])
    ]

    return NormalizedOrder(
        buyer_id        = payload.get("buyer_id", "unknown"),
        order_lines     = order_lines,
        origin_zip      = payload.get("origin_zip", "00000"),
        destination_zip = payload.get("destination_zip", "00000"),
        service_level   = payload.get("service_level", "standard"),
        protocol        = "ucp",
        raw_payload     = payload,
        cart_mandate    = payload.get("cart_mandate"),
        buyer_dnsid     = buyer_dnsid,
        payment_ref     = None,
    )
