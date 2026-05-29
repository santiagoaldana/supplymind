"""
UCP Catalog Generator — Phase 2: The Semantic Layer

PROTOCOL: UCP (Universal Commerce Protocol)
Format: JSON-LD (JSON with Linked Data context)

JSON-LD adds a @context block to regular JSON. That context is a dictionary
that maps every field name to a globally agreed definition. For example:
  "price" -> https://schema.org/price  (everyone agrees what price means)
  "sku"   -> https://schema.org/sku    (everyone agrees what sku means)

This means any Buyer Agent — built by anyone, anywhere — can read this
catalog and understand it without custom integration work.

UCP builds on JSON-LD and adds commerce-specific conventions:
  /.well-known/ucp.json  — where to find the catalog (the convention)
  @type: ItemList        — this is a list of products
  @type: Offer           — each product is an offer to sell

Phase 3 note: the Buyer Agent will fetch this URL as its first action,
read the catalog, and select products to purchase — no MCP tool call needed.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.inventory_server.db import init_db, get_connection


def generate_ucp_catalog(
    base_url: str = "http://localhost:8080",
    price_multiplier: float = 1.0,
    seller_name: str = "SupplyMind Seller",
) -> dict:
    init_db()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM products WHERE stock_qty > 0 ORDER BY category, sku"
    ).fetchall()
    conn.close()

    items = []
    for i, row in enumerate(rows, 1):
        price = round(row["unit_price"] * price_multiplier, 2)
        items.append({
            "@type": "ListItem",
            "position": i,
            "item": {
                "@type": "Product",
                "@id": f"{base_url}/products/{row['sku']}",

                "sku":         row["sku"],
                "name":        row["name"],
                "category":    row["category"],
                "description": row["description"],

                "offers": {
                    "@type":         "Offer",
                    "priceCurrency": "USD",
                    "price":         price,
                    "unitCode":      row["unit_of_measure"],

                    "availability": (
                        "https://schema.org/InStock"
                        if row["stock_qty"] > 0
                        else "https://schema.org/OutOfStock"
                    ),
                    "inventoryLevel": {
                        "@type": "QuantitativeValue",
                        "value": row["stock_qty"],
                        "unitText": row["unit_of_measure"],
                    },

                    "acceptedPaymentMethod": {
                        "@type": "PaymentMethod",
                        "name":    "USDC",
                        "network": "Ethereum Sepolia testnet",
                        "note":    "Circle Programmable Wallet. Phase 4 activates settlement."
                    },

                    "seller": {
                        "@type":         "Organization",
                        "name":          seller_name,
                        "walletAddress": row["wallet_address"]
                    }
                }
            }
        })

    return {
        "@context":    "https://schema.org",
        "@type":       "ItemList",
        "name":        f"{seller_name} Product Catalog",
        "description": "UCP-compliant catalog for autonomous B2B procurement. Machine-readable via JSON-LD.",
        "url":         f"{base_url}/.well-known/ucp.json",
        "numberOfItems": len(items),
        "itemListElement": items,

        "provider": {
            "@type": "Organization",
            "name":  seller_name,
            "url":   f"{base_url}/.well-known/kya.json"
        }
    }


if __name__ == "__main__":
    catalog = generate_ucp_catalog()
    out_path = Path(__file__).parent / "well_known" / "ucp.json"
    out_path.write_text(json.dumps(catalog, indent=2))
    print(f"UCP catalog written to {out_path}")
    print(f"  {catalog['numberOfItems']} products included")
