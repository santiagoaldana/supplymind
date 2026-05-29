"""
Phase 5A — Full End-to-End Demo

One command runs the entire SupplyMind protocol stack:

  DISCOVERY     A2A    — Buyer fetches Seller Agent Card
  CATALOG       UCP    — Buyer reads machine-readable product catalog
  IDENTITY      KYA    — Buyer verifies Seller identity
  QUOTE         x402   — Bulk quote with micro-payment gate
  ORDER         A2A    — Buyer sends purchase task, polls status
  GOVERNANCE    AP2    — Human creates Mandate (spending policy)
  PAYMENT CHECK ACF    — Tiered autonomy: AUTO / NOTIFY / BLOCK
  SETTLEMENT    MPP    — Dual-rail: Stripe Test (fiat) + simulated USDC

The seller server is spawned as a subprocess so only one terminal is needed.
Human approval prompt appears for any BLOCK-tier payment.
"""

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

import src.buyer_agent.buyer as buyer_module
from src.buyer_agent.buyer import (
    fetch_agent_card,
    fetch_ucp_catalog,
    select_products,
    request_bulk_quote,
    send_purchase_task,
    poll_task_status,
    SELLER_BASE_URL,
    BUYER_ID,
    PROCUREMENT_POLICY,
)

# Override shopping list to use small quantities that exercise all three ACF tiers:
#   DSK-002 $3.49 x1 = $3.49  → AUTO   (under $5)
#   PEN-001 $5.99 x1 = $5.99  → NOTIFY ($5-$10)
#   PPR-001 $14.99 x1 = $14.99 → BLOCK  (over $10)
DEMO_SHOPPING_LIST = [
    {"category": "desk",  "name_contains": "Whiteboard Markers", "quantity": 1},
    {"category": "pens",  "name_contains": "Ballpoint",          "quantity": 1},
    {"category": "paper", "name_contains": "Copy Paper",         "quantity": 1},
]
buyer_module.SHOPPING_LIST = DEMO_SHOPPING_LIST
from src.payment_server.mandate import create_mandate, check_mandate, record_spend, get_mandate
from src.payment_server.rails import execute_payment

console = Console()

SELLER_ID = "did:web:localhost:8080"


def start_seller_server() -> subprocess.Popen:
    console.print("[dim]Starting seller server...[/dim]")
    proc = subprocess.Popen(
        [sys.executable, "src/seller_agent/server.py"],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Wait until the agent-card endpoint is available (not just /)
    for _ in range(30):
        try:
            r = httpx.get(f"{SELLER_BASE_URL}/.well-known/agent-card.json", timeout=1.0)
            if r.status_code == 200:
                console.print("  Seller server   : [green]ready[/green]")
                return proc
        except Exception:
            pass
        time.sleep(0.5)
    console.print("[red]Seller server did not start in time.[/red]")
    proc.terminate()
    sys.exit(1)


def run_payment_layer(
    mandate_id: str,
    line_items: list[dict],
    quotes: dict[str, dict],
) -> list[dict]:
    """
    For each ordered item: AP2 check → ACF decision → MPP dual-rail execution.
    Returns list of payment result dicts for the final report.
    """
    console.print()
    console.rule("[bold cyan]Payment Layer — AP2 + ACF + MPP")

    results = []

    for item in line_items:
        sku    = item["sku"]
        quote  = quotes.get(sku)
        price  = quote["quoted_unit_price"] if quote else item["unit_price"]
        amount = round(price * item["quantity"], 2)

        console.print(f"\n  [cyan]{sku}[/cyan] {item['name']}  ${amount:.2f}")

        check    = check_mandate(mandate_id, amount, SELLER_ID)
        decision = check["decision"]

        tier_labels = {"approve": "[green]AUTO[/green]", "notify": "[yellow]NOTIFY[/yellow]", "block": "[red]BLOCK[/red]"}
        console.print(f"  ACF decision    : {tier_labels.get(decision, decision)}  {check['reason']}")

        acf_decision = decision

        if decision == "block":
            remaining = check.get("remaining_limit", "N/A")
            remaining_str = f"${remaining:.2f}" if isinstance(remaining, float) else str(remaining)
            console.print(Panel(
                f"[red]BLOCK: ${amount:.2f} blocked.[/red]\n"
                f"Reason: {check['reason']}\n"
                f"Product: {item['name']}\nRemaining mandate: {remaining_str}",
                title="[bold red]Human Approval Required",
                border_style="red",
            ))
            try:
                answer = input("  Approve this payment? [Y/n]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                answer = "n"
            approved = answer in ("", "y", "yes")
            console.print(f"  Human decision  : [{'green' if approved else 'red'}]{'APPROVED' if approved else 'DENIED'}[/{'green' if approved else 'red'}]")

            if not approved:
                results.append({
                    "sku": sku, "name": item["name"], "amount": amount,
                    "acf": "BLOCK", "outcome": "DENIED",
                    "fiat_ref": "N/A", "usdc_ref": "N/A",
                })
                continue
            acf_decision = "approve"

        payment = execute_payment(
            acf_decision=acf_decision,
            amount_usd=amount,
            seller_id=SELLER_ID,
            wallet_address=item["wallet_address"],
            mandate_id=mandate_id,
            description=f"{sku} — {item['name']}",
        )

        if payment.get("status") == "executed":
            record_spend(mandate_id, amount)
            fiat = payment["fiat"]
            usdc = payment["usdc"]
            console.print(f"  Fiat (Stripe)   : [green]{fiat['status']}[/green]  {fiat.get('reference', 'N/A')}")
            console.print(f"  USDC (simulated): [cyan]{usdc['status']}[/cyan]  {usdc['reference'][:22]}...")
            if payment.get("notification"):
                console.print(f"  [yellow]Notification[/yellow]: {payment['notification']}")

            tier_map = {"approve": "AUTO", "notify": "NOTIFY", "block": "BLOCK"}
            results.append({
                "sku": sku, "name": item["name"], "amount": amount,
                "acf": tier_map.get(decision, decision.upper()),
                "outcome": "EXECUTED",
                "fiat_ref": fiat.get("reference", "N/A"),
                "usdc_ref": usdc["reference"][:22] + "...",
            })

    return results


def print_final_report(
    mandate_id:     str,
    task:           dict,
    quotes:         dict[str, dict],
    payment_results: list[dict],
) -> None:
    console.print()
    console.rule("[bold green]Phase 5A — Full Stack Report")

    # Protocol trace table
    proto_table = Table(box=box.SIMPLE, title="Protocol Trace", show_lines=False)
    proto_table.add_column("Step", style="dim", width=4)
    proto_table.add_column("Protocol", style="cyan", width=10)
    proto_table.add_column("Action", style="white")
    proto_table.add_column("Result", style="green")

    rows = [
        ("1", "A2A",  "GET /.well-known/agent-card.json",  "Seller discovered"),
        ("2", "UCP",  "GET /.well-known/ucp.json",          "15 products loaded"),
        ("3", "KYA",  "GET /.well-known/kya.json",          "Seller identity verified"),
        ("4", "x402", "GET /quotes/{sku}",                  "Bulk quote (402 gate)"),
        ("5", "A2A",  "POST /tasks/send",                   f"Order {task['task_id'][:8]}... {task['status']}"),
        ("6", "AP2",  "create_mandate()",                   f"Mandate {mandate_id[:8]}..."),
        ("7", "ACF",  "check_mandate() per item",           "AUTO / NOTIFY / BLOCK"),
        ("8", "MPP",  "execute_payment() dual rail",        "Stripe + USDC settled"),
    ]
    for r in rows:
        proto_table.add_row(*r)
    console.print(proto_table)

    # Payment results table
    pay_table = Table(box=box.ROUNDED, show_lines=True, title="Payment Results")
    pay_table.add_column("SKU",      style="cyan", no_wrap=True)
    pay_table.add_column("Amount",   justify="right", style="green")
    pay_table.add_column("ACF Tier", justify="center")
    pay_table.add_column("Outcome",  justify="center")
    pay_table.add_column("Stripe Ref", style="dim")
    pay_table.add_column("USDC Ref",   style="dim")

    for r in payment_results:
        tier_color    = {"AUTO": "green", "NOTIFY": "yellow", "BLOCK": "red"}.get(r["acf"], "white")
        outcome_color = "green" if r["outcome"] == "EXECUTED" else "red"
        pay_table.add_row(
            r["sku"],
            f"${r['amount']:.2f}",
            f"[{tier_color}]{r['acf']}[/{tier_color}]",
            f"[{outcome_color}]{r['outcome']}[/{outcome_color}]",
            r["fiat_ref"],
            r["usdc_ref"],
        )
    console.print(pay_table)

    final_mandate = get_mandate(mandate_id)
    console.print(Panel(
        f"Protocols used  : A2A + UCP + KYA + x402 + AP2 + ACF + MPP\n"
        f"Mandate ID      : [cyan]{mandate_id}[/cyan]\n"
        f"Transactions    : [green]{final_mandate['tx_count']}[/green]\n"
        f"Total spent     : [green]${final_mandate['spent_total_usd']:.2f}[/green]"
        f"  of [dim]${final_mandate['max_total_usd']:.2f}[/dim] mandate limit\n"
        f"Remaining       : [green]${final_mandate['max_total_usd'] - final_mandate['spent_total_usd']:.2f}[/green]\n\n"
        f"[dim]Rails: Stripe Test Mode (fiat) + Simulated USDC\n"
        f"Cost: zero — Stripe test mode, USDC simulated, no LLM calls[/dim]",
        title="[bold]SupplyMind Phase 5A Summary",
        border_style="green",
    ))


def run() -> None:
    console.rule("[bold blue]SupplyMind Phase 5A — Full End-to-End Demo")
    console.print()
    console.print("[bold]Stack:[/bold] A2A + UCP + KYA + x402 + AP2 + ACF + MPP")
    console.print("[bold]Cost:[/bold]  zero — no LLM calls, Stripe test mode, USDC simulated")
    console.print()

    server_proc = start_seller_server()

    try:
        with httpx.Client(timeout=10.0) as client:
            # ── Phase 3 layer: discovery + catalog + quotes + order ──────────
            console.rule("[bold cyan]Discovery + Order Layer — A2A + UCP + KYA + x402")

            card     = fetch_agent_card(client)
            products = fetch_ucp_catalog(client)

            # KYA identity check
            console.print()
            console.print("  [bold cyan]3. Verifying Seller Identity[/bold cyan]  [dim](Protocol: KYA)[/dim]")
            kya = client.get(f"{SELLER_BASE_URL}/.well-known/kya.json").json()
            console.print(f"  Seller DID      : [green]{kya.get('id', 'N/A')}[/green]")
            console.print(f"  Seller name     : [green]{kya.get('name', 'N/A')}[/green]")

            selected = select_products(products)
            if not selected:
                console.print("[red]No products matched. Aborting.[/red]")
                return

            quotes: dict[str, dict] = {}
            for item in selected:
                if item["quantity"] > PROCUREMENT_POLICY["require_bulk_quote_above_qty"]:
                    quote = request_bulk_quote(client, item["sku"], item["quantity"])
                    quotes[item["sku"]] = quote

            task       = send_purchase_task(client, selected, quotes)
            final_task = poll_task_status(client, task["task_id"])

            if final_task["status"] != "completed":
                console.print(f"[red]Order failed: {final_task.get('errors')}[/red]")
                return

            line_items = final_task["result"]["line_items"]

            # ── Phase 4 layer: mandate + ACF + dual-rail payment ─────────────
            console.print()
            console.rule("[bold cyan]Governance Layer — AP2 Mandate")
            mandate = create_mandate(
                buyer_id=BUYER_ID,
                approved_sellers=[SELLER_ID],
                max_per_tx_usd=200.00,
                max_total_usd=500.00,
            )
            mandate_id = mandate["mandate_id"]
            console.print(f"  Mandate ID      : [cyan]{mandate_id}[/cyan]")
            console.print(f"  Per-tx limit    : [green]${mandate['max_per_tx_usd']:.2f}[/green]")
            console.print(f"  Total limit     : [green]${mandate['max_total_usd']:.2f}[/green]")
            console.print(f"  ACF tiers       : AUTO <$5 | NOTIFY $5-$10 | BLOCK >$10")

            payment_results = run_payment_layer(mandate_id, line_items, quotes)
            print_final_report(mandate_id, final_task, quotes, payment_results)

    except httpx.ConnectError:
        console.print("[red]Could not connect to seller server.[/red]")
        sys.exit(1)
    finally:
        server_proc.terminate()
        server_proc.wait()
        console.print("\n[dim]Seller server stopped.[/dim]")


if __name__ == "__main__":
    run()
