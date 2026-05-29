"""
Google UCP Profile Generator — Phase 5C

PROTOCOL: Google Universal Commerce Protocol (v2026-04-08)

The UCP Profile is served at /.well-known/ucp and is a capability declaration —
not a product list. It tells any UCP-compliant buyer agent:
  - What version of UCP this seller supports
  - Where the UCP service endpoints are
  - What capabilities are available (checkout, catalog, orders)
  - What payment handlers are configured (Stripe SPT)

This is the entry point for the Google UCP flow. The buyer fetches this first,
then POSTs to /ucp/v1/checkout-sessions to begin a transaction.

Contrast with our Phase 2 UCP (/.well-known/ucp.json):
  Phase 2: product list (what do you sell?)
  Google UCP: capability declaration (what can we do together?)
"""

import os
from dotenv import load_dotenv

load_dotenv()


def generate_ucp_profile(
    base_url:    str = "http://localhost:8080",
    seller_name: str = "SupplyMind Seller",
) -> dict:
    publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_placeholder")

    return {
        "ucp": {
            "version": "2026-04-08",
            "seller": {
                "name": seller_name,
                "did":  f"did:web:{base_url.replace('http://', '').replace('https://', '')}",
            },
            "services": {
                "dev.ucp.shopping": [
                    {
                        "version":   "2026-04-08",
                        "transport": "rest",
                        "endpoint":  f"{base_url}/ucp/v1",
                        "schema":    "https://ucp.dev/2026-04-08/services/shopping/rest.openapi.json",
                    }
                ]
            },
            "capabilities": {
                "dev.ucp.shopping.checkout": [{"version": "2026-04-08"}],
                "dev.ucp.shopping.catalog":  [{"version": "2026-04-08"}],
                "dev.ucp.shopping.orders":   [{"version": "2026-04-08"}],
            },
            "payment_handlers": {
                "com.stripe.spt": [
                    {
                        "id":      "stripe_test",
                        "version": "2026-04-08",
                        "config":  {"publishable_key": publishable_key},
                    }
                ]
            },
            "catalog_endpoint": f"{base_url}/.well-known/ucp.json",
            "identity_endpoint": f"{base_url}/.well-known/kya.json",
        }
    }
