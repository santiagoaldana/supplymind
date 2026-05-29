"""
Phase 8 -- Real USDC Settlement via Circle Programmable Wallets

WHAT THIS SHOWS:
  The USDC payment rail is no longer simulated. When Circle credentials are
  present, every payment executes a real blockchain transaction on Ethereum
  Sepolia testnet. The tx_hash returned is verifiable at
  https://sepolia.etherscan.io

TWO MODES:
  With CIRCLE_API_KEY + CIRCLE_BUYER_WALLET_ID in .env:
    -> Real Circle API calls, real Sepolia transactions, real tx hashes
    -> Copy any tx_hash and paste into sepolia.etherscan.io to verify on-chain

  Without Circle credentials:
    -> Simulated fallback (Phase 4 behavior, zero cost)
    -> All other phases continue to work unchanged

HOW TO GET CIRCLE CREDENTIALS (free, 5 minutes):
  1. Go to developers.circle.com
  2. Create a free account
  3. In the dashboard, switch to Sandbox mode
  4. Copy your API key -> CIRCLE_API_KEY in .env
  5. Your sandbox wallet ID is shown in the dashboard -> CIRCLE_BUYER_WALLET_ID

COST: zero -- Circle sandbox is free, Sepolia ETH is free testnet tokens.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.payment_server.circle_client import is_configured as circle_is_configured
from src.payment_server.rails import execute_payment
from src.payment_server.mandate import create_mandate, check_mandate, record_spend
from src.buyer_agent.buyer import (
    fetch_agent_card,
    fetch_ucp_catalog,
    select_products,
    send_purchase_task,
    poll_task_status,
    SELLER_BASE_URL,
)
import src.buyer_agent.buyer as buyer_module

buyer_module.SHOPPING_LIST = [
    {"category": "desk", "name_contains": "Whiteboard Markers", "quantity": 1},
]

console = Console()

BUYER_WALLET_ID  = os.getenv("CIRCLE_BUYER_WALLET_ID", "")
MANDATE_POLICY   = {
    "buyer_id":          "did:web:localhost:8090",
    "approved_sellers":  ["did:web:localhost:8080"],
    "max_per_tx_usd":    50.00,
    "max_total_usd":     500.00,
}


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


def run() -> None:
    circle_live = circle_is_configured() and bool(BUYER_WALLET_ID)

    console.rule("[bold blue]SupplyMind Phase 8 -- Real USDC Settlement")
    console.print()

    mode_table = Table(box=box.SIMPLE, show_header=False)
    mode_table.add_column("Field", style="dim", width=22)
    mode_table.add_column("Value")
    mode_table.add_row(
        "USDC rail",
        "[green]REAL -- Circle Programmable Wallets[/green]" if circle_live
        else "[yellow]SIMULATED -- add CIRCLE_API_KEY to .env for real settlement[/yellow]"
    )
    mode_table.add_row("Fiat rail",  "[green]REAL -- Stripe test mode[/green]")
    mode_table.add_row("Blockchain", "Ethereum Sepolia testnet" if circle_live else "N/A (simulated)")
    mode_table.add_row("Cost",       "zero -- sandbox/testnet only")
    console.print(mode_table)
    console.print()

    if not circle_live:
        console.print(Panel(
            "Circle credentials not found in .env\n\n"
            "To enable real USDC settlement:\n"
            "  1. Go to developers.circle.com (free account)\n"
            "  2. Switch to Sandbox mode in the dashboard\n"
            "  3. Copy API key -> CIRCLE_API_KEY in .env\n"
            "  4. Copy wallet ID -> CIRCLE_BUYER_WALLET_ID in .env\n\n"
            "Running in simulation mode -- all existing tests still pass.",
            title="[yellow]Simulation Mode[/yellow]",
            border_style="yellow",
        ))
        console.print()

    # ── Step 1: AP2 Mandate ──────────────────────────────────────────────────
    console.rule("[bold cyan]Step 1: Create AP2 Spending Mandate")
    mandate = create_mandate(**MANDATE_POLICY)
    mandate_id = mandate["mandate_id"]

    mandate_table = Table(box=box.SIMPLE, show_header=False)
    mandate_table.add_column("Field", style="dim", width=22)
    mandate_table.add_column("Value", style="green")
    mandate_table.add_row("Mandate ID",       mandate_id)
    mandate_table.add_row("Approved sellers", str(MANDATE_POLICY["approved_sellers"]))
    mandate_table.add_row("Max per tx",       f"${MANDATE_POLICY['max_per_tx_usd']:.2f}")
    mandate_table.add_row("Max total",        f"${MANDATE_POLICY['max_total_usd']:.2f}")
    mandate_table.add_row("Currency",         "USDC + USD (dual rail)")
    console.print(mandate_table)

    # ── Step 2: Procurement flow ─────────────────────────────────────────────
    console.rule("[bold cyan]Step 2: Procurement Flow (A2A + UCP)")
    console.print("  [dim]Starting seller server...[/dim]")
    proc = start_seller()
    console.print("  Seller server : [green]ready[/green]")
    console.print()

    try:
        with httpx.Client(timeout=10.0) as client:
            card     = fetch_agent_card(client)
            products = fetch_ucp_catalog(client)
            selected = select_products(products)
            task     = send_purchase_task(client, selected, {})
            final    = poll_task_status(client, task["task_id"])

        seller_did     = card.get("id", "did:web:localhost:8080")
        subtotal       = final.get("result", {}).get("products_subtotal", 0.0)
        purchased      = final.get("result", {}).get("purchased", [])
        seller_wallet  = final.get("result", {}).get("seller_wallet", "0x0000000000000000000000000000000000000000")

        console.print(f"  Order status  : [green]{final['status']}[/green]")
        console.print(f"  Items ordered : [green]{len(purchased)}[/green]")
        console.print(f"  Subtotal      : [green]${subtotal:.2f}[/green]")
        console.print(f"  Seller wallet : [dim]{seller_wallet}[/dim]")

    finally:
        proc.terminate()
        proc.wait()
        console.print()
        console.print("  [dim]Seller server stopped.[/dim]")

    # ── Step 3: ACF check + payment ──────────────────────────────────────────
    console.rule("[bold cyan]Step 3: ACF Decision + Dual-Rail Settlement")
    acf_result = check_mandate(mandate_id, subtotal, seller_did)
    acf        = acf_result.get("decision", "block")
    console.print(f"  ACF decision  : [{'green' if acf == 'approve' else 'yellow'}]{acf.upper()}[/{'green' if acf == 'approve' else 'yellow'}]")
    console.print()

    if circle_live:
        console.print("  [dim]Executing real Circle USDC transfer...[/dim]")
        console.print("  [dim]This may take 15-30 seconds for blockchain confirmation.[/dim]")
    else:
        console.print("  [dim]Executing simulated USDC transfer (no Circle credentials).[/dim]")
    console.print()

    result = execute_payment(
        acf_decision=acf,
        amount_usd=subtotal,
        seller_id=seller_did,
        wallet_address=seller_wallet,
        mandate_id=mandate_id,
        description=f"SupplyMind Phase 8 order {final['task_id']}",
    )

    if result.get("status") != "blocked":
        record_spend(mandate_id, subtotal)

    # ── Step 4: Print results ─────────────────────────────────────────────────
    console.rule("[bold cyan]Step 4: Settlement Results")

    fiat = result.get("fiat", {})
    usdc = result.get("usdc", {})

    results_table = Table(box=box.ROUNDED, show_lines=True, title="Payment Settlement")
    results_table.add_column("Rail",      style="dim",   width=8)
    results_table.add_column("Status",    style="green", width=12)
    results_table.add_column("Amount",    width=10)
    results_table.add_column("Reference / Tx Hash", width=50)

    fiat_ref = fiat.get("reference", "N/A") or "N/A"
    usdc_ref = usdc.get("reference", "N/A") or "N/A"

    results_table.add_row(
        "Fiat",
        fiat.get("status", "N/A"),
        f"${fiat.get('amount_usd', 0):.2f}",
        fiat_ref[:48],
    )
    results_table.add_row(
        "USDC",
        usdc.get("status", "N/A"),
        f"${usdc.get('amount_usd', 0):.2f}",
        usdc_ref[:48],
    )
    console.print(results_table)

    explorer_url = usdc.get("explorer_url", "")
    if explorer_url:
        console.print()
        console.print(f"  [bold]Blockchain explorer:[/bold]")
        console.print(f"  [green]{explorer_url}[/green]")
        console.print()
        console.print("  [dim]Paste that URL in your browser to see the real on-chain USDC transfer.[/dim]")

    # ── Summary ───────────────────────────────────────────────────────────────
    console.print()
    usdc_status = usdc.get("status", "simulated")
    console.print(Panel(
        f"Procurement       : [green]COMPLETE[/green] (A2A + UCP)\n"
        f"ACF decision      : [green]{acf.upper()}[/green]\n"
        f"Fiat settlement   : [green]{fiat.get('status', 'N/A').upper()}[/green] (Stripe test mode)\n"
        f"USDC settlement   : [{'green' if usdc_status == 'confirmed' else 'yellow'}]{usdc_status.upper()}[/{'green' if usdc_status == 'confirmed' else 'yellow'}] "
        f"({'Circle Sepolia testnet' if circle_live else 'simulated -- add Circle credentials for real'})\n\n"
        + (f"[dim]Tx hash: {usdc_ref[:64]}[/dim]\n"
           f"[dim]Verify : {explorer_url}[/dim]\n\n" if explorer_url else "")
        + f"[dim]Phase 8 completes the arc: protocols (1-5) -> identity (7) -> discovery (6) -> real settlement (8).[/dim]",
        title="[bold]Phase 8 Summary -- Real USDC Settlement",
        border_style="green",
    ))


if __name__ == "__main__":
    run()
