"""
Phase 5B — Multi-Seller Demo + Live Dashboard

Two seller agents run simultaneously on different ports.
The buyer agent discovers both, compares prices, and picks the
cheapest option per item across both catalogs.

Seller 1 (port 8080): SupplyMind Seller Agent — standard prices
Seller 2 (port 8081): QuickSupply Co.        — 15% higher prices overall
                       but 20% lower on pens (competitive specialty)

The buyer's rule: always pick the cheapest seller per item.
Result: some items go to Seller 1, pens go to Seller 2.

A live Rich dashboard updates in real time during the run.
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

from src.buyer_agent.buyer      import BUYER_ID, PROCUREMENT_POLICY
from src.buyer_agent.dashboard  import Dashboard, PaymentEvent
from src.payment_server.mandate import create_mandate, check_mandate, record_spend, get_mandate
from src.payment_server.rails   import execute_payment

console = Console()

SELLERS = [
    {
        "name":           "SupplyMind Seller",
        "port":           8080,
        "did":            "did:web:localhost:8080",
        "price_mult":     1.0,
        "well_known_dir": str(PROJECT_ROOT / "src/seller_agent/well_known"),
    },
    {
        "name":           "QuickSupply Co.",
        "port":           8081,
        "did":            "did:web:localhost:8081",
        "price_mult":     0.88,   # 12% cheaper overall — wins on most items
        "well_known_dir": str(PROJECT_ROOT / "src/seller_agent/well_known_seller2"),
    },
]

SHOPPING_LIST = [
    {"category": "desk",       "name_contains": "Whiteboard Markers", "quantity": 1},
    {"category": "pens",       "name_contains": "Ballpoint",          "quantity": 1},
    {"category": "paper",      "name_contains": "Copy Paper",         "quantity": 1},
    {"category": "stationery", "name_contains": "Binder Clips",       "quantity": 2},
]


def start_seller(seller: dict) -> subprocess.Popen:
    well_known = seller["well_known_dir"]
    proc = subprocess.Popen(
        [
            sys.executable, "src/seller_agent/server.py",
            "--port",             str(seller["port"]),
            "--name",             seller["name"],
            "--price-multiplier", str(seller["price_mult"]),
            "--well-known-dir",   well_known,
        ],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc


def wait_for_seller(port: int, timeout: int = 15) -> bool:
    url = f"http://localhost:{port}/.well-known/agent-card.json"
    for _ in range(timeout * 2):
        try:
            r = httpx.get(url, timeout=1.0)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def fetch_catalog(client: httpx.Client, seller: dict) -> list[dict]:
    base = f"http://localhost:{seller['port']}"
    resp = client.get(f"{base}/.well-known/ucp.json")
    resp.raise_for_status()
    catalog = resp.json()
    return [entry["item"] for entry in catalog["itemListElement"]]


def select_best_products(
    catalogs: dict[str, list[dict]],
    shopping_list: list[dict],
) -> list[dict]:
    """
    For each shopping list item, find the cheapest match across all sellers.
    Returns list of selected items with seller info attached.
    """
    selected = []
    for want in shopping_list:
        best = None
        for seller_name, products in catalogs.items():
            matches = [
                p for p in products
                if p["category"] == want["category"]
                and want["name_contains"].lower() in p["name"].lower()
                and p["offers"]["availability"].endswith("InStock")
            ]
            if not matches:
                continue
            cheapest = min(matches, key=lambda p: p["offers"]["price"])
            if best is None or cheapest["offers"]["price"] < best["offers"]["price"]:
                best = cheapest
                best = dict(cheapest)
                best["_seller_name"] = seller_name
                best["_quantity"]    = want["quantity"]

        if best:
            selected.append({
                "sku":            best["sku"],
                "name":           best["name"],
                "quantity":       best["_quantity"],
                "unit_price":     best["offers"]["price"],
                "wallet_address": best["offers"]["seller"]["walletAddress"],
                "seller_name":    best["_seller_name"],
                "seller_did":     next(
                    s["did"] for s in SELLERS if s["name"] == best["_seller_name"]
                ),
                "seller_port":    next(
                    s["port"] for s in SELLERS if s["name"] == best["_seller_name"]
                ),
            })
    return selected


def send_order(client: httpx.Client, port: int, items: list[dict], buyer_id: str) -> dict:
    order_lines = [{"sku": it["sku"], "quantity": it["quantity"]} for it in items]
    payload = {
        "buyer_id":        buyer_id,
        "order_lines":     order_lines,
        "origin_zip":      "90001",
        "destination_zip": "10001",
        "service_level":   "standard",
        "notes":           "Phase 5B multi-seller procurement run",
    }
    resp = client.post(f"http://localhost:{port}/tasks/send", json=payload)
    if resp.status_code in (201, 422):
        return resp.json()
    resp.raise_for_status()
    return resp.json()


def run() -> None:
    procs = []
    dashboard = Dashboard()

    try:
        # ── Start both sellers ─────────────────────────────────────────────
        console.rule("[bold blue]SupplyMind Phase 5B — Multi-Seller + Live Dashboard")
        console.print()

        seller_status = [
            {"name": s["name"], "did": s["did"], "port": s["port"], "ready": False}
            for s in SELLERS
        ]
        dashboard.set_sellers(seller_status)

        for seller in SELLERS:
            proc = start_seller(seller)
            procs.append(proc)

        with dashboard.live():
            dashboard.set_status("Starting seller servers...")

            for i, seller in enumerate(SELLERS):
                ready = wait_for_seller(seller["port"])
                seller_status[i]["ready"] = ready
                dashboard.set_sellers(seller_status)
                if not ready:
                    dashboard.set_status(f"[red]Seller {seller['name']} failed to start[/red]")
                    return

            dashboard.set_status("Both sellers ready. Fetching catalogs...")
            time.sleep(0.3)

            with httpx.Client(timeout=10.0) as client:
                # ── Fetch both catalogs ────────────────────────────────────
                catalogs: dict[str, list[dict]] = {}
                for seller in SELLERS:
                    products = fetch_catalog(client, seller)
                    catalogs[seller["name"]] = products

                dashboard.set_status(
                    f"Catalogs loaded: {sum(len(v) for v in catalogs.values())} products across {len(SELLERS)} sellers"
                )
                time.sleep(0.3)

                # ── Select best products ───────────────────────────────────
                selected = select_best_products(catalogs, SHOPPING_LIST)
                dashboard.set_status(f"Selected {len(selected)} items. Creating mandate...")
                time.sleep(0.3)

                # ── Create mandate ─────────────────────────────────────────
                mandate = create_mandate(
                    buyer_id=BUYER_ID,
                    approved_sellers=[s["did"] for s in SELLERS],
                    max_per_tx_usd=200.00,
                    max_total_usd=500.00,
                )
                mandate_id = mandate["mandate_id"]
                dashboard.set_mandate(mandate)
                dashboard.set_status("Mandate created. Sending orders...")
                time.sleep(0.3)

                # ── Group items by seller and send orders ──────────────────
                by_seller: dict[str, list[dict]] = {}
                for item in selected:
                    by_seller.setdefault(item["seller_name"], []).append(item)

                tasks = {}
                for seller_name, items in by_seller.items():
                    port = items[0]["seller_port"]
                    task = send_order(client, port, items, BUYER_ID)
                    tasks[seller_name] = task
                    dashboard.set_status(f"Order sent to {seller_name}: {task['status']}")
                    time.sleep(0.2)

                # ── Execute payments ───────────────────────────────────────
                dashboard.set_status("Executing payments...")

                for item in selected:
                    amount = round(item["unit_price"] * item["quantity"], 2)
                    check  = check_mandate(mandate_id, amount, item["seller_did"])
                    decision = check["decision"]

                    acf_tier_label = {"approve": "AUTO", "notify": "NOTIFY", "block": "BLOCK"}.get(decision, decision.upper())

                    if decision == "block":
                        # For the dashboard demo, auto-deny BLOCK items without prompt
                        # (interactive prompt breaks Live display)
                        ev = PaymentEvent(
                            sku=item["sku"], name=item["name"], seller=item["seller_name"],
                            amount=amount, acf_tier="BLOCK", outcome="BLOCKED",
                        )
                        dashboard.add_event(ev)
                        dashboard.set_status(f"BLOCKED: {item['sku']} ${amount:.2f} — requires human approval")
                        time.sleep(0.5)
                        continue

                    payment = execute_payment(
                        acf_decision=decision,
                        amount_usd=amount,
                        seller_id=item["seller_did"],
                        wallet_address=item["wallet_address"],
                        mandate_id=mandate_id,
                        description=f"{item['sku']} from {item['seller_name']}",
                    )

                    if payment.get("status") == "executed":
                        record_spend(mandate_id, amount)
                        fiat = payment["fiat"]
                        usdc = payment["usdc"]
                        ev = PaymentEvent(
                            sku=item["sku"], name=item["name"], seller=item["seller_name"],
                            amount=amount, acf_tier=acf_tier_label, outcome="EXECUTED",
                            fiat_ref=fiat.get("reference", "N/A"),
                            usdc_ref=usdc.get("reference", "N/A"),
                        )
                        dashboard.add_event(ev)
                        dashboard.set_mandate(get_mandate(mandate_id))
                        dashboard.set_status(f"Executed: {item['sku']} ${amount:.2f} [{acf_tier_label}]")
                        time.sleep(0.4)

                dashboard.set_status("All payments complete.")
                time.sleep(1.0)

        # ── Final comparison report ────────────────────────────────────────
        console.print()
        console.rule("[bold green]Phase 5B — Final Report")

        # Price comparison table
        comp_table = Table(box=box.ROUNDED, show_lines=True, title="Price Comparison — Winner Highlighted")
        comp_table.add_column("SKU",       style="cyan", no_wrap=True)
        comp_table.add_column("Product",   style="white")
        comp_table.add_column("Seller 1 Price", justify="right")
        comp_table.add_column("Seller 2 Price", justify="right")
        comp_table.add_column("Winner",    justify="center", style="bold")
        comp_table.add_column("Savings",   justify="right", style="green")

        s1_prods = {p["sku"]: p["offers"]["price"] for p in catalogs[SELLERS[0]["name"]]}
        s2_prods = {p["sku"]: p["offers"]["price"] for p in catalogs[SELLERS[1]["name"]]}

        total_savings = 0.0
        for item in selected:
            sku   = item["sku"]
            p1    = s1_prods.get(sku)
            p2    = s2_prods.get(sku)
            if p1 is None or p2 is None:
                continue
            winner = SELLERS[0]["name"] if p1 <= p2 else SELLERS[1]["name"]
            saving = abs(p1 - p2) * item["quantity"]
            total_savings += saving
            w_label = f"[green]{winner}[/green]"
            comp_table.add_row(
                sku, item["name"][:32],
                f"${p1:.2f}", f"${p2:.2f}",
                w_label,
                f"${saving:.2f}",
            )

        console.print(comp_table)

        final_mandate = get_mandate(mandate_id)
        console.print(Panel(
            f"Sellers compared  : {len(SELLERS)}\n"
            f"Items procured    : [green]{len(selected)}[/green]\n"
            f"Total savings     : [green]${total_savings:.2f}[/green] vs. single-seller baseline\n"
            f"Mandate spent     : [green]${final_mandate['spent_total_usd']:.2f}[/green]"
            f" of [dim]${final_mandate['max_total_usd']:.2f}[/dim]\n"
            f"Transactions      : [green]{final_mandate['tx_count']}[/green]\n\n"
            f"[dim]Protocols: A2A (x2 sellers) + UCP (x2 catalogs) + AP2 + ACF + MPP[/dim]",
            title="[bold]Multi-Seller Summary",
            border_style="green",
        ))

    finally:
        for proc in procs:
            proc.terminate()
            proc.wait()
        console.print("\n[dim]Both seller servers stopped.[/dim]")


if __name__ == "__main__":
    run()
