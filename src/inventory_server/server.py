"""
Inventory MCP Server — Phase 1: The Nervous System

PROTOCOL: MCP (Model Context Protocol) — The Integration Layer
Transport: stdio (JSON-RPC 2.0 over stdin/stdout)

MCP gives Claude a set of named actions (Tools) and readable data objects (Resources).
This server exposes the SupplyMind product catalog stored in SQLite.

MCP Wire Flow for a tool call:
  Host sends:    {"jsonrpc":"2.0","method":"tools/call","params":{"name":"list_products","arguments":{}},"id":1}
  Server reads:  stdin
  Server runs:   the decorated Python function
  Server writes: {"jsonrpc":"2.0","result":{"content":[{"type":"text","text":"[...]"}]},"id":1}
  Host reads:    stdout

wallet_address is included in every product response. Phase 4 (AP2/MPP) will use
this address to route USDC payment to the seller's Circle Programmable Wallet.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp.server.fastmcp import FastMCP
from src.inventory_server.db import init_db, get_connection

init_db()

mcp = FastMCP(
    "SupplyMind Inventory",
    instructions=(
        "You are the SupplyMind inventory system. "
        "Use list_products to browse the catalog, get_product to fetch full detail "
        "including the seller wallet_address, and check_stock to confirm availability "
        "before committing to a purchase."
    ),
)


@mcp.tool()
def list_products(category: str | None = None) -> list[dict]:
    """
    Return all products in the catalog, optionally filtered by category.

    MCP Tool: called by the Host when Claude needs to browse available inventory.
    Categories available: paper, pens, toner, stationery, desk.
    """
    conn = get_connection()
    if category:
        rows = conn.execute(
            "SELECT * FROM products WHERE category = ? ORDER BY sku",
            (category.lower(),),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM products ORDER BY category, sku").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@mcp.tool()
def get_product(sku: str) -> dict:
    """
    Return full product detail for a given SKU.

    MCP Tool: returns all fields including wallet_address.
    The wallet_address is the Circle Programmable Wallet that will receive
    USDC payment for this product in Phase 4 (AP2 Mandate execution).
    Returns an error dict if SKU is not found.
    """
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE sku = ?", (sku.upper(),)).fetchone()
    conn.close()
    if not row:
        return {"error": f"SKU {sku} not found"}
    return dict(row)


@mcp.tool()
def check_stock(sku: str, quantity: int) -> dict:
    """
    Check whether the requested quantity is available for a given SKU.

    MCP Tool: called before committing to a purchase to avoid ordering
    items that are out of stock. Returns available=True/False plus current stock level.
    """
    conn = get_connection()
    row = conn.execute(
        "SELECT sku, name, stock_qty, unit_of_measure FROM products WHERE sku = ?",
        (sku.upper(),),
    ).fetchone()
    conn.close()
    if not row:
        return {"error": f"SKU {sku} not found"}
    available = row["stock_qty"] >= quantity
    return {
        "sku": row["sku"],
        "name": row["name"],
        "requested_quantity": quantity,
        "stock_qty": row["stock_qty"],
        "unit_of_measure": row["unit_of_measure"],
        "available": available,
        "shortfall": max(0, quantity - row["stock_qty"]),
    }


@mcp.resource("inventory://catalog")
def get_catalog() -> str:
    """
    MCP Resource: the full product catalog as a JSON string.

    URI scheme: inventory://catalog
    Resources in MCP are readable data objects (like a file or a DB view).
    Phase 2 will replace this with a UCP-formatted JSON-LD catalog so machines
    can understand product semantics, not just raw field values.
    """
    conn = get_connection()
    rows = conn.execute("SELECT * FROM products ORDER BY category, sku").fetchall()
    conn.close()
    return json.dumps([dict(r) for r in rows], indent=2)


if __name__ == "__main__":
    # MCP stdio transport: server reads JSON-RPC from stdin, writes to stdout.
    # The Host (test_phase1.py) launches this as a subprocess and communicates
    # via pipes — no network port, no authentication, no cloud dependency.
    mcp.run()
