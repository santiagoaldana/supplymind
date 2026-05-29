"""
Shipping MCP Server — Phase 1: The Nervous System

PROTOCOL: MCP (Model Context Protocol) — The Integration Layer
Transport: stdio (JSON-RPC 2.0 over stdin/stdout)

This server exposes shipping estimation as MCP Tools.
No real carrier API is called — pricing uses a deterministic formula.
The purpose is to show a second MCP Server running alongside the Inventory Server,
both connected to the same Host (test_phase1.py) simultaneously.

Phase 3 note: When the Seller Agent becomes an HTTP service (A2A protocol),
this server will need to switch from stdio to SSE transport so multiple
Buyer Agents can connect concurrently.
"""

import json
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "SupplyMind Shipping",
    instructions=(
        "You are the SupplyMind shipping estimator. "
        "Use estimate_shipping to get a cost and delivery ETA for a shipment. "
        "Use list_service_levels to see all available speed tiers before estimating."
    ),
)

RATES: dict[str, dict] = {
    "economy":   {"base": 4.99,  "per_lb": 0.35, "eta": "7 business days"},
    "standard":  {"base": 8.99,  "per_lb": 0.55, "eta": "3 business days"},
    "express":   {"base": 19.99, "per_lb": 1.20, "eta": "1 business day"},
    "overnight": {"base": 39.99, "per_lb": 2.50, "eta": "Next day AM"},
}


@mcp.tool()
def estimate_shipping(
    origin_zip: str,
    destination_zip: str,
    weight_lbs: float,
    service_level: str = "standard",
) -> dict:
    """
    Return estimated shipping cost (USD) and delivery ETA.

    MCP Tool: called by the Host when Claude needs logistics cost before
    completing a procurement recommendation.

    Formula: total_cost = base_rate + (weight_lbs * per_lb_rate)
    No real carrier API is used — this is a deterministic stub suitable for
    Phase 1 testing. Phase 3 will replace this with live carrier quotes.
    """
    level = service_level.lower()
    if level not in RATES:
        return {
            "error": f"Unknown service level '{service_level}'. "
                     f"Valid options: {', '.join(RATES.keys())}"
        }
    rate = RATES[level]
    total_cost = round(rate["base"] + weight_lbs * rate["per_lb"], 2)
    return {
        "origin_zip": origin_zip,
        "destination_zip": destination_zip,
        "weight_lbs": weight_lbs,
        "service_level": level,
        "base_rate_usd": rate["base"],
        "per_lb_rate_usd": rate["per_lb"],
        "total_cost_usd": total_cost,
        "estimated_delivery": rate["eta"],
    }


@mcp.tool()
def list_service_levels() -> list[dict]:
    """
    Return all available shipping service levels with their rates.

    MCP Tool: called by the Host so Claude can present options to the buyer
    before committing to a service level.
    """
    return [
        {
            "service_level": level,
            "base_rate_usd": info["base"],
            "per_lb_rate_usd": info["per_lb"],
            "estimated_delivery": info["eta"],
        }
        for level, info in RATES.items()
    ]


@mcp.resource("shipping://rates")
def get_rate_card() -> str:
    """
    MCP Resource: the full shipping rate card as a JSON string.

    URI scheme: shipping://rates
    Phase 2 will expose this as a UCP-formatted price schedule so the
    Buyer Agent can compare rates programmatically without calling a tool.
    """
    return json.dumps(
        [
            {
                "service_level": level,
                "base_rate_usd": info["base"],
                "per_lb_rate_usd": info["per_lb"],
                "estimated_delivery": info["eta"],
            }
            for level, info in RATES.items()
        ],
        indent=2,
    )


if __name__ == "__main__":
    mcp.run()
