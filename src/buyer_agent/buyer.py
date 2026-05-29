"""
Buyer Agent — Phase 3: The Marketplace

PROTOCOLS USED IN ORDER:

1. A2A (Agent-to-Agent) — Discovery
   Fetches /.well-known/agent-card.json from the Seller to discover
   capabilities and the task endpoint URL.

2. UCP (Universal Commerce Protocol) — Catalog Reading
   Fetches /.well-known/ucp.json and parses the JSON-LD catalog
   to find matching products by category/name.

3. x402 (HTTP 402 Payment Required) — Micro-Settlement
   When requesting a bulk quote that exceeds the $500 threshold,
   the Seller responds with 402. The Buyer automatically:
     a. Reads the payment challenge
     b. Simulates a USDC micro-payment (Phase 4 does this for real)
     c. Retries the request with X-Payment header
     d. Receives the discounted bulk quote

4. A2A Task Lifecycle — Purchase Order
   Sends a structured purchase task to POST /tasks/send.
   Polls GET /tasks/{id} to confirm the order was accepted.

AUTONOMY MODEL:
  No human approves each step. The agent follows a rule-based decision tree:
    - Always buy the cheapest option in each required category
    - Never exceed the per-order budget (set in PROCUREMENT_POLICY)
    - Always request a bulk quote for quantities > 20
    - Always poll task status before reporting success

COST: zero. All requests go to localhost. USDC payment is simulated.
"""

import json
import sys
import time
from pathlib import Path

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

console = Console()

SELLER_BASE_URL = "http://localhost:8080"
BUYER_ID        = "did:web:localhost:8090"

PROCUREMENT_POLICY = {
    "max_order_value_usd": 2000.00,
    "require_bulk_quote_above_qty": 20,
    "preferred_service_level": "standard",
    "origin_zip": "90001",
    "destination_zip": "10001",
}

SHOPPING_LIST = [
    {"category": "paper", "name_contains": "Copy Paper", "quantity": 100},
    {"category": "pens",  "name_contains": "Ballpoint",  "quantity": 50},
]


def step(label: str, protocol: str) -> None:
    console.print(f"\n[bold cyan]{label}[/bold cyan]  [dim](Protocol: {protocol})[/dim]")


def fetch_agent_card(client: httpx.Client) -> dict:
    """
    A2A Protocol — Step 1: Discovery.
    The Buyer's very first action is to fetch the Seller's Agent Card.
    This tells the Buyer what the Seller can do and where to send tasks.
    The path /.well-known/agent-card.json is defined by the A2A specification.
    """
    step("1. Fetching Seller Agent Card", "A2A — Discovery")
    resp = client.get(f"{SELLER_BASE_URL}/.well-known/agent-card.json")
    resp.raise_for_status()
    card = resp.json()

    console.print(f"  Seller name       : [green]{card['name']}[/green]")
    console.print(f"  Seller DID        : [green]{card['identity']['did']}[/green]")
    console.print(f"  Task endpoint     : [green]{card['task_endpoint']}[/green]")
    caps = [c["id"] for c in card["capabilities"]]
    console.print(f"  Capabilities      : [green]{', '.join(caps)}[/green]")
    return card


def fetch_ucp_catalog(client: httpx.Client) -> list[dict]:
    """
    UCP Protocol — Step 2: Read the machine-readable catalog.
    The Buyer fetches the JSON-LD catalog and extracts products.
    Because every field uses schema.org definitions, no custom
    parsing logic is needed — the structure is always predictable.
    """
    step("2. Reading UCP Product Catalog", "UCP — Semantic Layer")
    resp = client.get(f"{SELLER_BASE_URL}/.well-known/ucp.json")
    resp.raise_for_status()
    catalog = resp.json()

    products = [entry["item"] for entry in catalog["itemListElement"]]
    console.print(f"  Catalog contains  : [green]{len(products)} products[/green]")
    console.print(f"  JSON-LD context   : [green]{catalog['@context']}[/green]")
    return products


def select_products(products: list[dict]) -> list[dict]:
    """
    Rule-based product selection — no LLM needed.
    Finds the cheapest matching product for each shopping list item.
    """
    step("3. Selecting Products from Catalog", "Rule-based logic (no LLM)")
    selected = []

    for want in SHOPPING_LIST:
        matches = [
            p for p in products
            if p["category"] == want["category"]
            and want["name_contains"].lower() in p["name"].lower()
            and p["offers"]["availability"].endswith("InStock")
        ]
        if not matches:
            console.print(f"  [red]No match found for: {want['name_contains']}[/red]")
            continue

        cheapest = min(matches, key=lambda p: p["offers"]["price"])
        selected.append({
            "sku":            cheapest["sku"],
            "name":           cheapest["name"],
            "quantity":       want["quantity"],
            "unit_price":     cheapest["offers"]["price"],
            "wallet_address": cheapest["offers"]["seller"]["walletAddress"],
        })
        console.print(
            f"  Selected [green]{cheapest['sku']}[/green] "
            f"{cheapest['name']} x{want['quantity']} "
            f"@ ${cheapest['offers']['price']:.2f}"
        )

    return selected


def request_bulk_quote(client: httpx.Client, sku: str, quantity: int) -> dict:
    """
    x402 Protocol — Step 4: Request a bulk quote.

    x402 Wire Flow:
      Attempt 1: GET /quotes/{sku}?quantity={qty}
        If order value <= $500 → 200 OK, quote returned immediately
        If order value >  $500 → 402 Payment Required, payment challenge in body

      On 402:
        Read the challenge: amount, currency, payTo address
        Simulate paying (Phase 4: real Circle USDC transaction)
        Attempt 2: retry with X-Payment header containing simulated tx hash
        → 200 OK, discounted bulk quote returned
    """
    step(f"4. Requesting Bulk Quote for {sku} x{quantity}", "x402 — Micro-Settlement Layer")

    resp = client.get(f"{SELLER_BASE_URL}/quotes/{sku}", params={"quantity": quantity})

    if resp.status_code == 402:
        challenge = resp.json()
        console.print(f"  [yellow]HTTP 402 Payment Required[/yellow]")
        console.print(f"  Fee required      : [yellow]{challenge['amount']} {challenge['currency']}[/yellow]")
        console.print(f"  Pay to wallet     : [yellow]{challenge['payTo']}[/yellow]")
        console.print(f"  [dim]{challenge['description']}[/dim]")

        # Simulate USDC payment (Phase 4 replaces this with a real Circle API call)
        simulated_tx_hash = "0xSIMULATED_TX_" + sku + "_" + str(quantity)
        console.print(f"  [dim]Simulating USDC payment...[/dim]")
        console.print(f"  Simulated tx hash : [green]{simulated_tx_hash}[/green]")

        # Retry with X-Payment header — x402 protocol
        resp = client.get(
            f"{SELLER_BASE_URL}/quotes/{sku}",
            params={"quantity": quantity},
            headers={"X-Payment": simulated_tx_hash},
        )
        resp.raise_for_status()
        quote = resp.json()
        console.print(f"  [green]402 resolved[/green] — bulk quote received after payment")
    else:
        resp.raise_for_status()
        quote = resp.json()
        console.print(f"  [green]Quote received[/green] (no payment required, order under ${500:.0f})")

    console.print(
        f"  Quoted price      : ${quote['quoted_unit_price']:.4f} "
        f"(discount: {quote['bulk_discount_pct']}%)"
    )
    console.print(f"  Quoted total      : [green]${quote['quoted_total']:.2f}[/green]")
    return quote


def send_purchase_task(client: httpx.Client, selected: list[dict], quotes: dict[str, dict]) -> dict:
    """
    A2A Protocol — Step 5: Send the purchase task.

    A2A Task Payload:
      buyer_id     : the Buyer Agent's DID (its identity)
      order_lines  : list of {sku, quantity}
      shipping info: origin_zip, destination_zip, service_level

    The Seller assigns a task_id and processes the order.
    Status: submitted -> completed | failed
    """
    step("5. Sending Purchase Task to Seller", "A2A — Task Lifecycle")

    order_lines = [{"sku": item["sku"], "quantity": item["quantity"]} for item in selected]

    payload = {
        "buyer_id":        BUYER_ID,
        "order_lines":     order_lines,
        "origin_zip":      PROCUREMENT_POLICY["origin_zip"],
        "destination_zip": PROCUREMENT_POLICY["destination_zip"],
        "service_level":   PROCUREMENT_POLICY["preferred_service_level"],
        "notes":           "Buyer Agent autonomous procurement run — Phase 3 test",
    }

    console.print(f"  POST /tasks/send")
    console.print(f"  Buyer ID          : [green]{BUYER_ID}[/green]")
    console.print(f"  Order lines       : [green]{order_lines}[/green]")

    resp = client.post(f"{SELLER_BASE_URL}/tasks/send", json=payload)

    if resp.status_code in (201, 422):
        task = resp.json()
    else:
        resp.raise_for_status()
        task = resp.json()

    console.print(f"  Task ID           : [green]{task['task_id']}[/green]")
    console.print(f"  Task status       : [green]{task['status']}[/green]")
    return task


def poll_task_status(client: httpx.Client, task_id: str) -> dict:
    """
    A2A Protocol — Step 6: Poll task status.
    The Buyer checks GET /tasks/{id} to confirm the order is completed.
    In a production A2A system this would use webhooks instead of polling.
    """
    step(f"6. Polling Task Status", "A2A — Task Lifecycle")
    resp = client.get(f"{SELLER_BASE_URL}/tasks/{task_id}")
    resp.raise_for_status()
    task = resp.json()
    console.print(f"  Task ID           : [green]{task['task_id']}[/green]")
    console.print(f"  Final status      : [green]{task['status']}[/green]")
    return task


def print_final_report(task: dict, quotes: dict[str, dict]) -> None:
    console.print()
    console.rule("[bold green]Procurement Report")

    if task["status"] != "completed" or not task.get("result"):
        console.print(Panel(
            f"[red]Order failed[/red]\nErrors: {task.get('errors', [])}",
            title="Result", border_style="red"
        ))
        return

    result = task["result"]
    lines  = result["line_items"]

    items_table = Table(box=box.ROUNDED, show_lines=True, title="Order Lines")
    items_table.add_column("SKU",        style="cyan",  no_wrap=True)
    items_table.add_column("Product",    style="white")
    items_table.add_column("Qty",        justify="right")
    items_table.add_column("Unit Price", justify="right", style="green")
    items_table.add_column("Total",      justify="right", style="green")
    items_table.add_column("Wallet (Phase 4)", style="dim")

    for li in lines:
        sku   = li["sku"]
        quote = quotes.get(sku)
        price = quote["quoted_unit_price"] if quote else li["unit_price"]
        total = round(price * li["quantity"], 2)
        items_table.add_row(
            sku,
            li["name"],
            f"{li['quantity']} {li['unit_of_measure']}",
            f"${price:.4f}",
            f"${total:.2f}",
            li["wallet_address"][:18] + "...",
        )

    console.print(items_table)

    products_total = sum(
        round((quotes[li["sku"]]["quoted_unit_price"] if li["sku"] in quotes else li["unit_price"]) * li["quantity"], 2)
        for li in lines
    )

    console.print(Panel(
        f"Task ID          : [cyan]{task['task_id']}[/cyan]\n"
        f"Status           : [green]{task['status']}[/green]\n"
        f"Products total   : [green]${products_total:.2f}[/green]\n"
        f"Shipping         : [dim]calculated by MCP Shipping Server at execution[/dim]\n\n"
        f"[dim]Phase 4: AP2 Mandate will authorize USDC settlement\n"
        f"to each product wallet_address listed above.[/dim]",
        title="[bold]Summary",
        border_style="green",
    ))


def run() -> None:
    console.rule("[bold blue]SupplyMind Buyer Agent — Phase 3")
    console.print()
    console.print("[bold]Protocols:[/bold] A2A (discovery + tasks) + UCP (catalog) + x402 (quotes)")
    console.print("[bold]Cost:[/bold]      zero — all requests to localhost, USDC simulated")
    console.print()

    with httpx.Client(timeout=10.0) as client:
        try:
            card     = fetch_agent_card(client)
            products = fetch_ucp_catalog(client)
            selected = select_products(products)

            if not selected:
                console.print("[red]No products matched the shopping list. Aborting.[/red]")
                return

            quotes: dict[str, dict] = {}
            for item in selected:
                if item["quantity"] > PROCUREMENT_POLICY["require_bulk_quote_above_qty"]:
                    quote = request_bulk_quote(client, item["sku"], item["quantity"])
                    quotes[item["sku"]] = quote

            task        = send_purchase_task(client, selected, quotes)
            final_task  = poll_task_status(client, task["task_id"])
            print_final_report(final_task, quotes)

        except httpx.ConnectError:
            console.print("[red]Connection refused.[/red] Is the seller server running?")
            console.print("  [cyan].venv/bin/python src/seller_agent/server.py[/cyan]")
            sys.exit(1)


# ── NANDA Discovery (Phase 6) ─────────────────────────────────────────────────

NANDA_SEARCH_URL = "https://nest.projectnanda.org/api/network/search"


def discover_via_nanda(
    capability: str = "urn:nanda:cap:ucp:catalog",
    tag: str = "office-supplies",
    timeout: float = 5.0,
) -> str | None:
    """
    Search the NANDA NEST registry for a seller agent.

    Returns the seller's endpoint URL if found, or None if NANDA is
    unreachable or returns no matches (caller falls back to SELLER_BASE_URL).

    NANDA search payload: {capability, tag}
    NANDA response:       [{name, endpoint, capabilities, did, ...}, ...]

    Why this matters: a real buyer agent does not hardcode seller URLs.
    It searches NANDA at startup, finds who sells what it needs, and
    contacts that seller -- without any prior knowledge of who they are.
    """
    try:
        r = httpx.post(
            NANDA_SEARCH_URL,
            json={"capability": capability, "tag": tag},
            timeout=timeout,
        )
        if r.status_code == 200:
            results = r.json()
            if isinstance(results, list) and results:
                endpoint = results[0].get("endpoint") or results[0].get("url")
                if endpoint:
                    return endpoint.rstrip("/")
    except Exception:
        pass
    return None


# ── Google UCP v2026-04-08 Flow ───────────────────────────────────────────────

def fetch_ucp_profile(client: httpx.Client) -> dict:
    """
    Google UCP Step 1: fetch the UCP Profile from /.well-known/ucp.
    The profile declares capabilities and payment handlers.
    This replaces the separate A2A agent-card + KYA fetches.
    """
    step("1. Fetching UCP Profile", "Google UCP v2026-04-08 — Capability Declaration")
    resp = client.get(f"{SELLER_BASE_URL}/.well-known/ucp")
    resp.raise_for_status()
    profile = resp.json()

    ucp = profile["ucp"]
    console.print(f"  UCP version     : [green]{ucp['version']}[/green]")
    console.print(f"  Seller          : [green]{ucp['seller']['name']}[/green]")
    console.print(f"  DID             : [green]{ucp['seller']['did']}[/green]")
    caps = list(ucp["capabilities"].keys())
    console.print(f"  Capabilities    : [green]{', '.join(caps)}[/green]")
    handlers = list(ucp["payment_handlers"].keys())
    console.print(f"  Payment handlers: [green]{', '.join(handlers)}[/green]")
    return profile


def create_checkout_session(client: httpx.Client, items: list[dict]) -> dict:
    """
    Google UCP Step 2: open a checkout session with line items.
    The seller validates stock, calculates totals, returns session_id.
    This replaces POST /tasks/send (A2A) + GET /quotes/{sku} (x402).
    """
    step("2. Creating Checkout Session", "Google UCP — POST /ucp/v1/checkout-sessions")
    line_items = [{"sku": it["sku"], "quantity": it["quantity"]} for it in items]
    payload = {"line_items": line_items, "buyer_id": BUYER_ID}

    resp = client.post(f"{SELLER_BASE_URL}/ucp/v1/checkout-sessions", json=payload)
    resp.raise_for_status()
    session = resp.json()

    console.print(f"  Session ID      : [green]{session['session_id']}[/green]")
    console.print(f"  Status          : [green]{session['status']}[/green]")
    console.print(f"  Subtotal        : [green]${session['subtotal_usd']:.2f}[/green]")
    console.print(f"  Payment handler : [green]{session['payment_handler']}[/green]")
    for li in session["line_items"]:
        console.print(
            f"  [dim]{li['sku']}  {li['name']}  x{li['quantity']}  "
            f"@ ${li['unit_price']:.2f}  = ${li['item_total']:.2f}[/dim]"
        )
    return session


def complete_checkout(client: httpx.Client, session_id: str, payment_token: str) -> dict:
    """
    Google UCP Step 3: submit payment token to confirm the order.
    In Phase 5C the token is simulated. Phase 8 uses a real Stripe SPT.
    This replaces the separate AP2 + MPP payment calls.
    """
    step("3. Completing Checkout", "Google UCP — POST /ucp/v1/checkout-sessions/{id}/complete")
    payload = {"payment_token": payment_token, "buyer_id": BUYER_ID}

    resp = client.post(
        f"{SELLER_BASE_URL}/ucp/v1/checkout-sessions/{session_id}/complete",
        json=payload,
    )
    resp.raise_for_status()
    result = resp.json()

    console.print(f"  Order ID        : [green]{result['order_id']}[/green]")
    console.print(f"  Status          : [green]{result['status']}[/green]")
    console.print(f"  Payment token   : [dim]{payment_token}[/dim]")
    return result


def get_order_status(client: httpx.Client, order_id: str) -> dict:
    """
    Google UCP Step 4: poll order status.
    This replaces GET /tasks/{id} (A2A task polling).
    """
    step("4. Checking Order Status", "Google UCP — GET /ucp/v1/orders/{id}")
    resp = client.get(f"{SELLER_BASE_URL}/ucp/v1/orders/{order_id}")
    resp.raise_for_status()
    order = resp.json()

    console.print(f"  Order ID        : [green]{order['order_id']}[/green]")
    console.print(f"  Protocol        : [green]{order.get('protocol', 'N/A')}[/green]")
    console.print(f"  Final status    : [green]{order['status']}[/green]")
    return order


def run_ucp_flow() -> None:
    """
    Google UCP v2026-04-08 buyer flow.
    4 steps vs the original 6-step multi-protocol flow.
    Runs alongside run() for side-by-side comparison in test_phase5c.py.
    """
    console.rule("[bold blue]SupplyMind Buyer — Google UCP Flow")
    console.print()
    console.print("[bold]Protocol:[/bold] Google UCP v2026-04-08 (single protocol, 4 calls)")
    console.print("[bold]Cost:[/bold]     zero — payment token simulated")
    console.print()

    with httpx.Client(timeout=10.0) as client:
        try:
            profile  = fetch_ucp_profile(client)

            # Reuse existing catalog + selection logic — product discovery
            # is separate from checkout in Google UCP
            products = fetch_ucp_catalog(client)
            selected = select_products(products)

            if not selected:
                console.print("[red]No products matched. Aborting.[/red]")
                return

            session = create_checkout_session(client, selected)
            token   = f"SIMULATED_SPT_{session['session_id'][:8]}"
            result  = complete_checkout(client, session["session_id"], token)
            order   = get_order_status(client, result["order_id"])

            console.print()
            console.print(Panel(
                f"Protocol        : [green]Google UCP v2026-04-08[/green]\n"
                f"Order ID        : [cyan]{order['order_id']}[/cyan]\n"
                f"Status          : [green]{order['status']}[/green]\n"
                f"Subtotal        : [green]${session['subtotal_usd']:.2f}[/green]\n\n"
                f"[dim]Steps: 4 calls, 1 protocol\n"
                f"Phase 8: payment_token becomes a real Stripe SPT or Circle tx hash[/dim]",
                title="[bold]Google UCP Summary",
                border_style="green",
            ))

        except httpx.ConnectError:
            console.print("[red]Connection refused.[/red] Is the seller server running?")
            sys.exit(1)


if __name__ == "__main__":
    run()
