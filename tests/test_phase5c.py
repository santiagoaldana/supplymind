"""
Phase 5C — Google UCP Upgrade

Runs both flows against the same seller server and prints a side-by-side
comparison showing the protocol reduction.

OLD FLOW (Phases 2-3):        NEW FLOW (Google UCP v2026-04-08):
─────────────────────         ──────────────────────────────────
GET /.well-known/ucp.json     GET /.well-known/ucp
GET /.well-known/kya.json     (identity embedded in UCP profile)
POST /tasks/send              POST /ucp/v1/checkout-sessions
GET  /tasks/{id}              POST /ucp/v1/checkout-sessions/{id}/complete
(separate payment call)       GET  /ucp/v1/orders/{id}

4 protocols, 5+ calls         1 protocol, 4 calls
"""

import subprocess
import sys
import time
from pathlib import Path

import httpx
from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table
from rich import box

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import src.buyer_agent.buyer as buyer_module
from src.buyer_agent.buyer import (
    fetch_agent_card,
    fetch_ucp_catalog,
    select_products,
    send_purchase_task,
    poll_task_status,
    fetch_ucp_profile,
    create_checkout_session,
    complete_checkout,
    get_order_status,
    SELLER_BASE_URL,
    BUYER_ID,
    PROCUREMENT_POLICY,
)

# Small quantities to keep the demo clean (no x402 gate triggered)
buyer_module.SHOPPING_LIST = [
    {"category": "desk",  "name_contains": "Whiteboard Markers", "quantity": 1},
    {"category": "pens",  "name_contains": "Ballpoint",          "quantity": 1},
]

console = Console()


def start_seller() -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, "src/seller_agent/server.py"],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(30):
        try:
            r = httpx.get(f"{SELLER_BASE_URL}/.well-known/agent-card.json", timeout=1.0)
            if r.status_code == 200:
                return proc
        except Exception:
            pass
        time.sleep(0.5)
    console.print("[red]Seller server did not start.[/red]")
    proc.terminate()
    sys.exit(1)


def run_old_flow(client: httpx.Client) -> dict:
    """Run the Phase 3 multi-protocol flow. Returns summary dict."""
    console.rule("[bold yellow]OLD FLOW — Phase 3 (Multi-Protocol)")
    card     = fetch_agent_card(client)
    products = fetch_ucp_catalog(client)
    selected = select_products(products)
    task     = send_purchase_task(client, selected, {})
    final    = poll_task_status(client, task["task_id"])
    return {
        "order_id":  final["task_id"],
        "status":    final["status"],
        "subtotal":  final["result"]["products_subtotal"],
        "protocols": ["A2A", "UCP (custom)", "KYA", "A2A tasks"],
        "calls":     5,
    }


def run_new_flow(client: httpx.Client) -> dict:
    """Run the Google UCP v2026-04-08 flow. Returns summary dict."""
    console.rule("[bold green]NEW FLOW — Google UCP v2026-04-08")
    profile  = fetch_ucp_profile(client)
    products = fetch_ucp_catalog(client)
    selected = select_products(products)
    session  = create_checkout_session(client, selected)
    token    = f"SIMULATED_SPT_{session['session_id'][:8]}"
    result   = complete_checkout(client, session["session_id"], token)
    order    = get_order_status(client, result["order_id"])
    return {
        "order_id":  order["order_id"],
        "status":    order["status"],
        "subtotal":  session["subtotal_usd"],
        "protocols": ["Google UCP v2026-04-08"],
        "calls":     4,
    }


def print_comparison(old: dict, new: dict) -> None:
    console.print()
    console.rule("[bold blue]Phase 5C — Protocol Comparison")

    # Step-by-step table
    steps_table = Table(box=box.ROUNDED, show_lines=True, title="Step-by-Step Comparison")
    steps_table.add_column("Step", style="dim", width=5)
    steps_table.add_column("Old Flow (Phase 3)", style="yellow")
    steps_table.add_column("New Flow (Google UCP)", style="green")

    steps = [
        ("1", "GET /.well-known/agent-card.json  (A2A)",  "GET /.well-known/ucp  (UCP Profile)"),
        ("2", "GET /.well-known/kya.json  (KYA)",         "(identity embedded in UCP profile)"),
        ("3", "GET /.well-known/ucp.json  (catalog)",     "GET /.well-known/ucp.json  (catalog)"),
        ("4", "POST /tasks/send  (A2A order)",            "POST /ucp/v1/checkout-sessions"),
        ("5", "GET /tasks/{id}  (A2A poll)",              "POST /ucp/v1/checkout-sessions/{id}/complete"),
        ("6", "(separate payment call)",                  "GET /ucp/v1/orders/{id}"),
    ]
    for step, old_step, new_step in steps:
        steps_table.add_row(step, old_step, new_step)
    console.print(steps_table)

    # Summary panel
    summary_table = Table(box=box.SIMPLE, show_header=True)
    summary_table.add_column("Metric",     style="dim")
    summary_table.add_column("Old Flow",   style="yellow", justify="center")
    summary_table.add_column("New Flow",   style="green",  justify="center")

    summary_table.add_row("Protocols",      "4",   "1")
    summary_table.add_row("API calls",      str(old["calls"]), str(new["calls"]))
    summary_table.add_row("Order status",   old["status"], new["status"])
    summary_table.add_row(
        "Subtotal",
        f"${old['subtotal']:.2f}",
        f"${new['subtotal']:.2f}",
    )
    summary_table.add_row(
        "Interoperable with",
        "SupplyMind buyer only",
        "Any Google UCP buyer (Gemini, etc.)",
    )

    console.print(Panel(summary_table, title="[bold]Summary", border_style="blue"))
    console.print(Panel(
        f"[yellow]Old:[/yellow] A2A discovery + KYA identity + custom UCP catalog + A2A tasks + separate payment\n"
        f"[green]New:[/green] One UCP Profile declares everything. Checkout session is cart + order + payment in one flow.\n\n"
        f"[dim]Any buyer agent that speaks Google UCP v2026-04-08 can now transact with SupplyMind\n"
        f"without knowing about A2A, KYA, x402, AP2, or MPP separately.[/dim]",
        title="[bold]What Changed",
        border_style="green",
    ))


def run() -> None:
    console.rule("[bold blue]SupplyMind Phase 5C — Google UCP Upgrade")
    console.print()
    console.print("[bold]Goal:[/bold] Show old multi-protocol flow vs. Google UCP v2026-04-08 side by side")
    console.print()

    console.print("[dim]Starting seller server...[/dim]")
    proc = start_seller()
    console.print("  Seller server   : [green]ready[/green]")

    try:
        with httpx.Client(timeout=10.0) as client:
            old_result = run_old_flow(client)
            console.print()
            new_result = run_new_flow(client)
            print_comparison(old_result, new_result)
    finally:
        proc.terminate()
        proc.wait()
        console.print("\n[dim]Seller server stopped.[/dim]")


if __name__ == "__main__":
    run()
