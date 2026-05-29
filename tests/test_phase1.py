"""
Phase 1 Integration Test — Direct MCP Tool Call Client

PROTOCOLS IN USE:
  MCP (Model Context Protocol) — The Integration Layer
  Transport: stdio (JSON-RPC 2.0 over subprocess pipes)

  This test client is the MCP HOST. It:
    1. Launches both MCP servers as subprocesses (stdio transport)
    2. Performs the MCP initialize handshake with each server
    3. Calls tools/list to discover what each server can do
    4. Calls tools/call directly to execute a procurement scenario
    5. Prints a structured procurement report — no LLM, no API cost

MCP WIRE FLOW (what happens under the hood for each tool call):

  Host sends over stdin:
    {
      "jsonrpc": "2.0",
      "method": "tools/call",
      "params": {"name": "list_products", "arguments": {"category": "paper"}},
      "id": 1
    }

  Server reads from stdin, runs the Python function, writes to stdout:
    {
      "jsonrpc": "2.0",
      "result": {"content": [{"type": "text", "text": "[{...}]"}]},
      "id": 1
    }

  Host reads stdout and parses the result.

This is JSON-RPC 2.0 — the same wire protocol used by language servers (LSP)
in VS Code, and by Ethereum nodes. MCP reuses it over stdio pipes instead of
a network socket.

COST: zero. No external API calls. Runs entirely on your laptop.
"""

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

VENV_PYTHON = str(PROJECT_ROOT / ".venv" / "bin" / "python")
INVENTORY_SERVER = str(PROJECT_ROOT / "src" / "inventory_server" / "server.py")
SHIPPING_SERVER = str(PROJECT_ROOT / "src" / "shipping_server" / "server.py")

console = Console()

# Procurement scenario: what the buyer wants to order
PROCUREMENT_ORDER = [
    {"sku": "PPR-001", "quantity": 5,  "weight_lbs": 50.0, "label": "Copy Paper (Case, 10 reams)"},
    {"sku": "PEN-001", "quantity": 20, "weight_lbs": 10.0, "label": "Ballpoint Pens (Box of 50)"},
]

ORIGIN_ZIP      = "10001"  # New York
DESTINATION_ZIP = "90001"  # Los Angeles
SERVICE_LEVEL   = "standard"


async def run_phase1_test() -> None:

    console.rule("[bold blue]SupplyMind Phase 1 — MCP Direct Tool Call Test")
    console.print()
    console.print("[bold]Protocol:[/bold] MCP (Model Context Protocol) over stdio transport")
    console.print("[bold]Transport:[/bold] JSON-RPC 2.0 via subprocess stdin/stdout pipes")
    console.print("[bold]Cost:[/bold] zero — no external API calls")
    console.print()

    # ── MCP STEP 1: Launch both servers as subprocesses ───────────────────────
    # StdioServerParameters tells the MCP client to start the server script
    # as a child process and communicate via its stdin/stdout pipes.
    # This is the stdio transport defined in the MCP specification.
    inventory_params = StdioServerParameters(
        command=VENV_PYTHON,
        args=[INVENTORY_SERVER],
        env=None,
    )
    shipping_params = StdioServerParameters(
        command=VENV_PYTHON,
        args=[SHIPPING_SERVER],
        env=None,
    )

    async with stdio_client(inventory_params) as (inv_read, inv_write):
        async with stdio_client(shipping_params) as (ship_read, ship_write):
            async with ClientSession(inv_read, inv_write) as inv_session:
                async with ClientSession(ship_read, ship_write) as ship_session:

                    # ── MCP STEP 2: Initialize handshake ──────────────────────
                    # MCP requires an 'initialize' request before any other call.
                    # The server responds with its name, version, and capabilities.
                    # Think of this as the "good morning, what can you do?" exchange.
                    await inv_session.initialize()
                    await ship_session.initialize()

                    console.print("[green]MCP handshake complete[/green] — both servers initialized")
                    console.print()

                    # ── MCP STEP 3: Tool discovery (tools/list) ───────────────
                    # tools/list is a standard MCP method. The server returns
                    # every tool it exposes, with name, description, and the
                    # JSON Schema that describes its input parameters.
                    inv_tools_resp  = await inv_session.list_tools()
                    ship_tools_resp = await ship_session.list_tools()

                    discovery_table = Table(
                        title="MCP Tool Discovery — tools/list",
                        box=box.ROUNDED,
                        show_lines=True,
                    )
                    discovery_table.add_column("Server",    style="cyan",  no_wrap=True)
                    discovery_table.add_column("Tool Name", style="green", no_wrap=True)
                    discovery_table.add_column("Description")

                    for t in inv_tools_resp.tools:
                        first_line = (t.description or "").split("\n")[0].strip()
                        discovery_table.add_row("inventory_server", t.name, first_line)
                    for t in ship_tools_resp.tools:
                        first_line = (t.description or "").split("\n")[0].strip()
                        discovery_table.add_row("shipping_server", t.name, first_line)

                    console.print(discovery_table)
                    console.print()

                    # ── MCP STEP 4: Execute procurement scenario ──────────────
                    # Each call below is a real MCP tools/call request over stdio.
                    # The JSON-RPC message is sent to the server subprocess,
                    # the server runs the Python function, and returns the result.

                    console.rule("[bold yellow]Procurement Scenario")
                    console.print(
                        f"  Buyer ZIP: [cyan]{ORIGIN_ZIP}[/cyan]  "
                        f"Seller ZIP: [cyan]{DESTINATION_ZIP}[/cyan]  "
                        f"Service: [cyan]{SERVICE_LEVEL}[/cyan]"
                    )
                    console.print()

                    line_items = []
                    total_product_cost = 0.0
                    total_weight = 0.0

                    for item in PROCUREMENT_ORDER:

                        # ── MCP tools/call: check_stock ───────────────────────
                        # Asks the inventory server whether requested qty is available.
                        # MCP method: tools/call
                        # Server: inventory_server
                        stock_result = await inv_session.call_tool(
                            "check_stock",
                            {"sku": item["sku"], "quantity": item["quantity"]},
                        )
                        stock = json.loads(stock_result.content[0].text)

                        # ── MCP tools/call: get_product ───────────────────────
                        # Fetches full product detail including unit_price and wallet_address.
                        # The wallet_address is what Phase 4 (AP2/MPP) will use to
                        # route USDC settlement to the seller's Circle wallet.
                        product_result = await inv_session.call_tool(
                            "get_product",
                            {"sku": item["sku"]},
                        )
                        product = json.loads(product_result.content[0].text)

                        subtotal = round(product["unit_price"] * item["quantity"], 2)
                        total_product_cost += subtotal
                        total_weight += item["weight_lbs"]

                        line_items.append({
                            "sku":            item["sku"],
                            "name":           product["name"],
                            "qty":            item["quantity"],
                            "uom":            product["unit_of_measure"],
                            "unit_price":     product["unit_price"],
                            "subtotal":       subtotal,
                            "available":      stock["available"],
                            "stock_qty":      stock["stock_qty"],
                            "wallet_address": product["wallet_address"],
                        })

                    # ── MCP tools/call: estimate_shipping ─────────────────────
                    # Asks the shipping server for cost and ETA for the full order.
                    # MCP method: tools/call
                    # Server: shipping_server
                    shipping_result = await ship_session.call_tool(
                        "estimate_shipping",
                        {
                            "origin_zip":      ORIGIN_ZIP,
                            "destination_zip": DESTINATION_ZIP,
                            "weight_lbs":      total_weight,
                            "service_level":   SERVICE_LEVEL,
                        },
                    )
                    shipping = json.loads(shipping_result.content[0].text)

                    total_cost = round(total_product_cost + shipping["total_cost_usd"], 2)

                    # ── Print procurement report ───────────────────────────────

                    items_table = Table(
                        title="Order Lines",
                        box=box.ROUNDED,
                        show_lines=True,
                    )
                    items_table.add_column("SKU",          style="cyan",  no_wrap=True)
                    items_table.add_column("Product",      style="white")
                    items_table.add_column("Qty",          justify="right")
                    items_table.add_column("Unit Price",   justify="right", style="green")
                    items_table.add_column("Subtotal",     justify="right", style="green")
                    items_table.add_column("In Stock?",    justify="center")
                    items_table.add_column("Wallet (Phase 4)", style="dim")

                    for li in line_items:
                        avail_str = "[green]Yes[/green]" if li["available"] else "[red]No[/red]"
                        items_table.add_row(
                            li["sku"],
                            li["name"],
                            f"{li['qty']} {li['uom']}",
                            f"${li['unit_price']:.2f}",
                            f"${li['subtotal']:.2f}",
                            avail_str,
                            li["wallet_address"][:20] + "...",
                        )

                    console.print(items_table)
                    console.print()

                    shipping_table = Table(
                        title="Shipping Estimate (MCP tools/call: estimate_shipping)",
                        box=box.ROUNDED,
                    )
                    shipping_table.add_column("Field",  style="cyan")
                    shipping_table.add_column("Value",  style="white")

                    shipping_table.add_row("Service Level",     shipping["service_level"])
                    shipping_table.add_row("Total Weight",      f"{shipping['weight_lbs']} lbs")
                    shipping_table.add_row("Base Rate",         f"${shipping['base_rate_usd']:.2f}")
                    shipping_table.add_row("Per-lb Rate",       f"${shipping['per_lb_rate_usd']:.2f}")
                    shipping_table.add_row("Shipping Cost",     f"${shipping['total_cost_usd']:.2f}")
                    shipping_table.add_row("Estimated Delivery",shipping["estimated_delivery"])

                    console.print(shipping_table)
                    console.print()

                    all_available = all(li["available"] for li in line_items)
                    status_color  = "green" if all_available else "red"
                    status_label  = "READY TO PROCURE" if all_available else "BLOCKED — STOCK ISSUE"

                    summary = (
                        f"Products subtotal : [green]${total_product_cost:.2f}[/green]\n"
                        f"Shipping cost     : [green]${shipping['total_cost_usd']:.2f}[/green]\n"
                        f"[bold]TOTAL             : [green]${total_cost:.2f}[/green][/bold]\n\n"
                        f"Status: [{status_color}]{status_label}[/{status_color}]\n\n"
                        f"[dim]Phase 4 note: each line item carries a wallet_address.\n"
                        f"The AP2 Mandate will authorize USDC settlement to those addresses\n"
                        f"once spending guardrails are satisfied.[/dim]"
                    )

                    console.print(Panel(
                        summary,
                        title="[bold]Procurement Summary",
                        border_style=status_color,
                    ))


if __name__ == "__main__":
    asyncio.run(run_phase1_test())
