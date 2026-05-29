"""
Phase 4 Integration Test — AP2 + ACF + MPP

Demonstrates the full payment governance stack without any LLM calls.

What this test does:
  1. Human creates a Mandate (spending policy)
  2. Buyer selects 3 products — one per ACF tier
  3. For each product:
       a. check_mandate → get ACF decision
       b. AUTO   → execute immediately, no prompt
       c. NOTIFY → execute + print notification
       d. BLOCK  → print approval prompt, wait for Y/N, then execute or stop
  4. Print final mandate state (spent, remaining, tx count)
  5. Print side-by-side rail results (Stripe fiat vs simulated USDC)

No server needed. Runs entirely in-process.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from src.payment_server.mandate import create_mandate, check_mandate, record_spend, get_mandate
from src.payment_server.rails   import execute_payment

console = Console()

BUYER_ID   = "did:web:localhost:8090"
SELLER_ID  = "did:web:localhost:8080"

# Three test items — one per ACF tier
ITEMS = [
    {
        "sku":            "DSK-002",
        "name":           "Whiteboard Markers (Set of 8)",
        "unit_price":     3.49,
        "quantity":       1,
        "wallet_address": "0x" + "a" * 40,
        "expected_tier":  "AUTO",
    },
    {
        "sku":            "PEN-001",
        "name":           "Ballpoint Pens (Box of 50)",
        "unit_price":     5.99,
        "quantity":       1,
        "wallet_address": "0x" + "b" * 40,
        "expected_tier":  "NOTIFY",
    },
    {
        "sku":            "PPR-001",
        "name":           "Copy Paper (Case, 10 reams)",
        "unit_price":     14.99,
        "quantity":       1,
        "wallet_address": "0x" + "c" * 40,
        "expected_tier":  "BLOCK",
    },
]


def print_acf_badge(decision: str) -> str:
    colors = {"approve": "green", "notify": "yellow", "block": "red"}
    labels = {"approve": "AUTO", "notify": "NOTIFY", "block": "BLOCK"}
    color = colors.get(decision, "white")
    label = labels.get(decision, decision.upper())
    return f"[{color}]{label}[/{color}]"


def run() -> None:
    console.rule("[bold blue]SupplyMind Phase 4 — AP2 + ACF + MPP Payment Demo")
    console.print()
    console.print("[bold]Protocols:[/bold] AP2 (mandate) + ACF (tiered autonomy) + MPP (dual-rail settlement)")
    console.print("[bold]Rails:[/bold]     Stripe Test Mode (fiat) + Simulated USDC")
    console.print("[bold]Cost:[/bold]      zero — Stripe test mode, USDC simulated")
    console.print()

    # ── Step 1: Create Mandate ────────────────────────────────────────────────
    console.rule("[bold cyan]Step 1: Human Creates Mandate (AP2)")
    mandate = create_mandate(
        buyer_id=BUYER_ID,
        approved_sellers=[SELLER_ID],
        max_per_tx_usd=50.00,
        max_total_usd=100.00,
    )
    mandate_id = mandate["mandate_id"]
    console.print(f"  Mandate ID      : [cyan]{mandate_id}[/cyan]")
    console.print(f"  Buyer           : [green]{BUYER_ID}[/green]")
    console.print(f"  Approved sellers: [green]{mandate['approved_sellers']}[/green]")
    console.print(f"  Per-tx limit    : [green]${mandate['max_per_tx_usd']:.2f}[/green]")
    console.print(f"  Total limit     : [green]${mandate['max_total_usd']:.2f}[/green]")
    console.print(f"  ACF tiers       : AUTO <$5 | NOTIFY $5-$10 | BLOCK >$10")

    results = []

    # ── Steps 2-4: Process each item ─────────────────────────────────────────
    for item in ITEMS:
        amount = round(item["unit_price"] * item["quantity"], 2)

        console.print()
        console.rule(f"[bold]{item['sku']} — {item['name']} (${amount:.2f})")

        # AP2: Check mandate
        check = check_mandate(mandate_id, amount, SELLER_ID)
        decision = check["decision"]
        console.print(f"  ACF Decision    : {print_acf_badge(decision)}")
        console.print(f"  Reason          : [dim]{check['reason']}[/dim]")

        if decision == "block":
            console.print()
            console.print(Panel(
                f"[red]BLOCK: ${amount:.2f} exceeds ACF threshold.[/red]\n"
                f"Seller: {SELLER_ID}\n"
                f"Product: {item['name']}\n"
                f"Mandate remaining: ${check['remaining_limit']:.2f}",
                title="[bold red]ACF BLOCK — Human Approval Required",
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
                    "sku": item["sku"], "amount": amount,
                    "acf": "BLOCK", "outcome": "DENIED by human",
                    "fiat_ref": "N/A", "usdc_ref": "N/A",
                })
                continue
            acf_decision = "approve"
        else:
            acf_decision = decision

        # MPP: Execute both rails
        payment = execute_payment(
            acf_decision=acf_decision,
            amount_usd=amount,
            seller_id=SELLER_ID,
            wallet_address=item["wallet_address"],
            mandate_id=mandate_id,
            description=f"{item['sku']} — {item['name']}",
        )

        if payment.get("status") == "executed":
            record_spend(mandate_id, amount)
            fiat = payment["fiat"]
            usdc = payment["usdc"]

            console.print(f"  Fiat (Stripe)   : [{('green' if fiat['status'] == 'succeeded' else 'yellow')}]{fiat['status']}[/{'green' if fiat['status'] == 'succeeded' else 'yellow'}]  ref={fiat['reference']}")
            console.print(f"  USDC (simulated): [cyan]{usdc['status']}[/cyan]  tx={usdc['reference'][:20]}...")

            if payment.get("notification"):
                console.print(f"  [yellow]Notification[/yellow]: {payment['notification']}")

            results.append({
                "sku":      item["sku"],
                "amount":   amount,
                "acf":      item["expected_tier"],
                "outcome":  "EXECUTED",
                "fiat_ref": fiat.get("reference", "N/A"),
                "usdc_ref": usdc.get("reference", "N/A")[:24] + "...",
            })
        else:
            results.append({
                "sku": item["sku"], "amount": amount,
                "acf": "BLOCK", "outcome": "BLOCKED",
                "fiat_ref": "N/A", "usdc_ref": "N/A",
            })

    # ── Final Report ─────────────────────────────────────────────────────────
    console.print()
    console.rule("[bold green]Phase 4 Payment Report")

    final_mandate = get_mandate(mandate_id)

    summary_table = Table(box=box.ROUNDED, show_lines=True, title="Payment Results")
    summary_table.add_column("SKU",       style="cyan", no_wrap=True)
    summary_table.add_column("Amount",    justify="right", style="green")
    summary_table.add_column("ACF Tier",  justify="center")
    summary_table.add_column("Outcome",   justify="center")
    summary_table.add_column("Stripe Ref", style="dim")
    summary_table.add_column("USDC Ref",   style="dim")

    for r in results:
        tier_color = {"AUTO": "green", "NOTIFY": "yellow", "BLOCK": "red"}.get(r["acf"], "white")
        outcome_color = "green" if r["outcome"] == "EXECUTED" else "red"
        summary_table.add_row(
            r["sku"],
            f"${r['amount']:.2f}",
            f"[{tier_color}]{r['acf']}[/{tier_color}]",
            f"[{outcome_color}]{r['outcome']}[/{outcome_color}]",
            r["fiat_ref"] if r["fiat_ref"] != "N/A" else "[dim]N/A[/dim]",
            r["usdc_ref"] if r["usdc_ref"] != "N/A" else "[dim]N/A[/dim]",
        )

    console.print(summary_table)

    console.print(Panel(
        f"Mandate ID     : [cyan]{mandate_id}[/cyan]\n"
        f"Transactions   : [green]{final_mandate['tx_count']}[/green]\n"
        f"Total spent    : [green]${final_mandate['spent_total_usd']:.2f}[/green]\n"
        f"Remaining      : [green]${final_mandate['max_total_usd'] - final_mandate['spent_total_usd']:.2f}[/green] "
        f"of [dim]${final_mandate['max_total_usd']:.2f}[/dim]\n\n"
        f"[dim]Protocols used: AP2 (mandate + check) + ACF (tiered decisions)\n"
        f"               + MPP (Stripe Test fiat) + MPP (simulated USDC)[/dim]",
        title="[bold]Mandate Summary",
        border_style="green",
    ))


if __name__ == "__main__":
    run()
