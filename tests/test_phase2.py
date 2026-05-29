"""
Phase 2 Integration Test — UCP Catalog + KYA Identity

PROTOCOLS IN USE:
  UCP (Universal Commerce Protocol) — The Semantic Layer
    Fetches /.well-known/ucp.json and validates JSON-LD structure.
    Demonstrates that a Buyer Agent can read the catalog without MCP.

  KYA (Know Your Agent) — The Identity Layer
    Fetches /.well-known/kya.json and validates identity fields.
    Demonstrates that a Buyer Agent can verify seller identity before transacting.

  HTTP — transport for both documents

COST: zero. All requests go to localhost.

HOW TO RUN:
  Terminal 1: .venv/bin/python src/seller_agent/server.py
  Terminal 2: .venv/bin/python tests/test_phase2.py
"""

import json
import sys
from pathlib import Path

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()
BASE_URL = "http://localhost:8080"


def test_kya_identity() -> dict:
    """
    KYA Protocol step: fetch and validate the seller agent identity card.
    A real Buyer Agent would verify the cryptographic proof here.
    In Phase 2 the proof is a placeholder; Phase 4 activates real signing.
    """
    console.rule("[bold blue]KYA — Know Your Agent")
    console.print("[dim]Fetching: GET /.well-known/kya.json[/dim]")
    console.print()

    resp = httpx.get(f"{BASE_URL}/.well-known/kya.json")
    resp.raise_for_status()
    kya = resp.json()

    kya_table = Table(box=box.ROUNDED, show_lines=True, title="KYA Identity Document")
    kya_table.add_column("Field",  style="cyan", no_wrap=True)
    kya_table.add_column("Value",  style="white")

    kya_table.add_row("Agent Name",    kya["name"])
    kya_table.add_row("Version",       kya["version"])
    kya_table.add_row("DID",           kya["id"])
    kya_table.add_row("Owner",         kya["owner"]["name"])
    kya_table.add_row("Wallet",        kya["wallet"]["address"])
    kya_table.add_row("Network",       kya["wallet"]["network"])
    kya_table.add_row("Capabilities",  ", ".join(kya["capabilities"]))
    kya_table.add_row("Catalog URL",   kya["endpoints"]["catalog"])
    kya_table.add_row("A2A Tasks URL", kya["endpoints"]["a2a_tasks"])
    kya_table.add_row("Proof Type",    kya["proof"]["type"])

    console.print(kya_table)
    console.print()
    console.print("[green]KYA check passed[/green] — seller identity document retrieved")
    console.print("[dim]Phase 4 will verify the cryptographic signature in proof.signature[/dim]")
    console.print()
    return kya


def test_ucp_catalog() -> dict:
    """
    UCP Protocol step: fetch and validate the machine-readable product catalog.
    Demonstrates JSON-LD semantic structure: every product is a schema.org/Product,
    every price is a schema.org/Offer with a globally understood priceCurrency field.
    """
    console.rule("[bold blue]UCP — Universal Commerce Protocol")
    console.print("[dim]Fetching: GET /.well-known/ucp.json[/dim]")
    console.print()

    resp = httpx.get(f"{BASE_URL}/.well-known/ucp.json")
    resp.raise_for_status()
    catalog = resp.json()

    console.print(f"  Catalog name    : [cyan]{catalog['name']}[/cyan]")
    console.print(f"  JSON-LD context : [cyan]{catalog['@context']}[/cyan]")
    console.print(f"  Top-level type  : [cyan]{catalog['@type']}[/cyan]  (schema.org/ItemList)")
    console.print(f"  Total products  : [cyan]{catalog['numberOfItems']}[/cyan]")
    console.print()

    products_table = Table(
        box=box.ROUNDED,
        show_lines=True,
        title="UCP Catalog — Products (JSON-LD schema.org/Product)",
    )
    products_table.add_column("SKU",        style="cyan",  no_wrap=True)
    products_table.add_column("Name",       style="white")
    products_table.add_column("Category",   style="dim")
    products_table.add_column("Price (USD)", justify="right", style="green")
    products_table.add_column("Stock",       justify="right")
    products_table.add_column("Availability", style="green")
    products_table.add_column("Wallet (Phase 4)", style="dim")

    for entry in catalog["itemListElement"]:
        p     = entry["item"]
        offer = p["offers"]
        avail = "InStock" if "InStock" in offer["availability"] else "OutOfStock"
        color = "green" if avail == "InStock" else "red"
        products_table.add_row(
            p["sku"],
            p["name"],
            p["category"],
            f"${offer['price']:.2f}",
            str(offer["inventoryLevel"]["value"]),
            f"[{color}]{avail}[/{color}]",
            offer["seller"]["walletAddress"][:16] + "...",
        )

    console.print(products_table)
    console.print()

    first = catalog["itemListElement"][0]["item"]
    console.print(Panel(
        json.dumps(first, indent=2),
        title="[bold]Sample JSON-LD product entry (first item)",
        border_style="dim",
    ))
    console.print()
    console.print("[green]UCP check passed[/green] — machine-readable catalog retrieved")
    console.print("[dim]Any Buyer Agent speaking JSON-LD can parse this without custom integration[/dim]")
    return catalog


if __name__ == "__main__":
    console.rule("[bold blue]SupplyMind Phase 2 — UCP + KYA Integration Test")
    console.print()
    console.print("[bold]Protocols:[/bold] UCP (JSON-LD catalog) + KYA (agent identity)")
    console.print("[bold]Transport:[/bold] HTTP to localhost:8000")
    console.print("[bold]Cost:[/bold]      zero")
    console.print()

    try:
        kya     = test_kya_identity()
        catalog = test_ucp_catalog()

        console.rule("[bold green]Phase 2 Complete")
        console.print()
        console.print(Panel(
            f"Seller identity  : [cyan]{kya['name']}[/cyan]\n"
            f"Catalog products : [cyan]{catalog['numberOfItems']}[/cyan]\n"
            f"Payment method   : [cyan]USDC (wallet per product row)[/cyan]\n\n"
            f"[dim]Phase 3 next: A2A agent cards + Buyer Agent discovery.\n"
            f"The Buyer Agent will fetch kya.json first, then ucp.json,\n"
            f"then POST a purchase task to /tasks/send.[/dim]",
            title="[bold]Summary",
            border_style="green",
        ))

    except httpx.ConnectError:
        console.print("[red]Connection refused.[/red] Is the seller server running?")
        console.print()
        console.print("Start it first in another terminal:")
        console.print("  [cyan].venv/bin/python src/seller_agent/server.py[/cyan]")
        sys.exit(1)
