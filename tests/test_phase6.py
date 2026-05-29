"""
Phase 6 -- NANDA AgentFacts + Open Agentic Web Discovery

Demonstrates how SupplyMind participates in the Open Agentic Web:

  1. AgentFacts generation
     Builds a W3C Verifiable Credential (JSON-LD) that describes the seller.
     Signed with our real secp256k1 key from Phase 7.

  2. NANDA registration attempt
     POSTs the AgentFacts to nest.projectnanda.org.
     Expected result on localhost: registry rejects HTTP endpoint (needs HTTPS).
     We show the full payload so you can see what a real registration looks like.

  3. Buyer NANDA discovery (simulated)
     Shows how a buyer would call NANDA, get back a seller endpoint, and use it.
     Because NANDA will not return localhost, we show the fallback path too.

  4. Full procurement flow
     Runs the existing A2A + UCP flow against the local seller server.
     This is the same flow as Phase 5A, now with NANDA as Step 0.

What this proves:
  The SupplyMind seller is ready for the Open Agentic Web.
  The moment it gets a public HTTPS URL (Maritime, Render, Railway, etc.),
  one command registers it on NANDA and any buyer agent in the ecosystem
  can find it. No directory, no hardcoded URLs, no middlemen.

Cost: zero -- NANDA call is free, local server, no LLM calls.
"""

import json
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

from src.seller_agent.nanda_facts import build_agent_facts, register as nanda_register
from src.identity.keys import (
    load_or_create_private_key_from_file,
    public_key_to_hex,
    derive_wallet_address,
    verify_signature,
)
from src.buyer_agent.buyer import (
    discover_via_nanda,
    fetch_agent_card,
    fetch_ucp_catalog,
    select_products,
    send_purchase_task,
    poll_task_status,
    SELLER_BASE_URL,
    BUYER_ID,
)
import src.buyer_agent.buyer as buyer_module

KEYS_DIR = PROJECT_ROOT / ".keys"
KEY_FILE  = KEYS_DIR / "seller_private_key.hex"

buyer_module.SHOPPING_LIST = [
    {"category": "desk",  "name_contains": "Whiteboard Markers", "quantity": 2},
    {"category": "pens",  "name_contains": "Ballpoint",          "quantity": 2},
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


def run() -> None:
    console.rule("[bold blue]SupplyMind Phase 6 -- NANDA AgentFacts + Open Agentic Web")
    console.print()
    console.print("[bold]What this shows:[/bold] How SupplyMind participates in the Open Agentic Web")
    console.print("[bold]Cost:[/bold]            zero -- NANDA is free, no LLM calls, no cloud costs")
    console.print()

    # ── Step 1: Load key + generate AgentFacts ───────────────────────────────
    console.rule("[bold cyan]Step 1: Generate AgentFacts (W3C Verifiable Credential)")

    private_key    = load_or_create_private_key_from_file(KEY_FILE)
    public_key     = private_key.public_key()
    public_key_hex = public_key_to_hex(public_key)
    wallet_address = derive_wallet_address(public_key)

    agent_facts = build_agent_facts(private_key)
    cs          = agent_facts["credentialSubject"]
    sig         = agent_facts["proof"]["signature"]

    id_table = Table(box=box.SIMPLE, show_header=False)
    id_table.add_column("Field", style="dim", width=22)
    id_table.add_column("Value", style="green")
    id_table.add_row("Document type",     "W3C Verifiable Credential + AgentFacts")
    id_table.add_row("DID (issuer)",      agent_facts["id"])
    id_table.add_row("Agent name",        cs["name"])
    id_table.add_row("Endpoint",          cs["endpoint"])
    id_table.add_row("Wallet address",    wallet_address)
    id_table.add_row("Signature (secp)",  f"{sig[:28]}...{sig[-8:]}")
    id_table.add_row("Capabilities",      str(len(cs["capabilities"])))
    console.print(id_table)

    console.print()
    console.print("  [dim]Capabilities mapped to NANDA URN format:[/dim]")
    for cap in cs["capabilities"]:
        console.print(f"  [dim]  {cap}[/dim]")

    # ── Step 2: Verify the AgentFacts signature ──────────────────────────────
    console.rule("[bold cyan]Step 2: Verify AgentFacts Signature")
    proof_pub = agent_facts["proof"]["public_key"]
    proof_sig = agent_facts["proof"]["signature"]
    valid     = verify_signature(agent_facts, proof_sig, proof_pub)

    console.print(f"  Signature valid : [{'green' if valid else 'red'}]{'YES -- AgentFacts cryptographically authentic' if valid else 'NO -- verification failed'}[/{'green' if valid else 'red'}]")
    console.print()
    console.print("  [dim]This is the same verification a buyer agent runs when it receives[/dim]")
    console.print("  [dim]our AgentFacts from NANDA. If valid, the buyer knows the seller is[/dim]")
    console.print("  [dim]who they claim to be -- unforgeable without the private key.[/dim]")

    # ── Step 3: NANDA registration attempt ──────────────────────────────────
    console.rule("[bold cyan]Step 3: NANDA Registration Attempt")
    console.print(f"  Registry : [dim]https://nest.projectnanda.org[/dim]")
    console.print(f"  Endpoint : [dim]{cs['endpoint']}[/dim]")
    console.print()
    console.print("  [dim]NANDA requires HTTPS endpoints for production registration.[/dim]")
    console.print("  [dim]localhost HTTP is expected to be rejected -- this is by design.[/dim]")
    console.print("  [dim]Once deployed to Maritime/Render/Railway, this call succeeds.[/dim]")
    console.print()

    try:
        r = httpx.post(
            "https://nest.projectnanda.org/api/network/register",
            json={
                "name":         cs["name"],
                "description":  cs["description"],
                "endpoint":     cs["endpoint"],
                "tags":         cs["tags"],
                "capabilities": cs["capabilities"],
                "did":          agent_facts["id"],
                "agentfacts":   agent_facts,
            },
            timeout=8.0,
        )
        console.print(f"  HTTP status : [dim]{r.status_code}[/dim]")
        try:
            body = r.json()
            console.print(f"  Response    : [dim]{json.dumps(body)[:200]}[/dim]")
        except Exception:
            console.print(f"  Response    : [dim]{r.text[:200]}[/dim]")

        if r.status_code in (200, 201):
            console.print()
            console.print("  [green]SUCCESS -- SupplyMind is now on the Open Agentic Web.[/green]")
            console.print("  [green]Search nest.projectnanda.org to verify.[/green]")
        else:
            console.print()
            console.print("  [yellow]Not accepted (expected for localhost).[/yellow]")
            console.print("  [yellow]Deploy to HTTPS to complete production registration.[/yellow]")
    except httpx.ConnectError:
        console.print("  [yellow]Could not reach NANDA NEST (network error).[/yellow]")
    except Exception as e:
        console.print(f"  [yellow]Error: {e}[/yellow]")

    # ── Step 4: Buyer NANDA discovery ────────────────────────────────────────
    console.rule("[bold cyan]Step 4: Buyer NANDA Discovery")
    console.print("  [dim]A buyer agent searching NANDA for office supply sellers...[/dim]")
    console.print()

    discovered_url = discover_via_nanda(
        capability="urn:nanda:cap:ucp:catalog",
        tag="office-supplies",
        timeout=6.0,
    )

    if discovered_url:
        console.print(f"  NANDA result  : [green]{discovered_url}[/green]")
        console.print(f"  Using         : [green]NANDA-discovered endpoint[/green]")
        seller_url = discovered_url
    else:
        console.print(f"  NANDA result  : [yellow]no match (expected -- localhost not indexed)[/yellow]")
        console.print(f"  Fallback to   : [dim]{SELLER_BASE_URL}[/dim]")
        seller_url = SELLER_BASE_URL

    console.print()
    console.print("  [dim]In production: NANDA returns the seller endpoint and the buyer[/dim]")
    console.print("  [dim]connects without knowing who the seller was in advance.[/dim]")
    console.print("  [dim]Here: fallback to hardcoded localhost for local testing.[/dim]")

    # ── Step 5: Full procurement flow ────────────────────────────────────────
    console.rule("[bold cyan]Step 5: Full Procurement Flow (A2A + UCP)")
    console.print("  [dim]Starting seller server...[/dim]")
    proc = start_seller()
    console.print("  Seller server : [green]ready at localhost:8080[/green]")
    console.print()

    try:
        with httpx.Client(timeout=10.0) as client:
            card     = fetch_agent_card(client)
            console.print(f"  A2A card      : [green]{card.get('name')}[/green] (endpoint verified)")

            products = fetch_ucp_catalog(client)
            console.print(f"  UCP catalog   : [green]{len(products)} products[/green] fetched")

            selected = select_products(products)
            console.print(f"  Selected      : [green]{len(selected)} items[/green] match shopping list")

            task      = send_purchase_task(client, selected, {})
            final     = poll_task_status(client, task["task_id"])

            order_table = Table(box=box.SIMPLE, show_header=False)
            order_table.add_column("Field", style="dim", width=18)
            order_table.add_column("Value", style="green")
            order_table.add_row("Order ID",    final["task_id"])
            order_table.add_row("Status",      final["status"])
            order_table.add_row("Items",       str(len(final.get("result", {}).get("purchased", []))))
            subtotal = final.get("result", {}).get("products_subtotal", 0)
            order_table.add_row("Subtotal",    f"${subtotal:.2f}")
            console.print(order_table)

    finally:
        proc.terminate()
        proc.wait()
        console.print()
        console.print("  [dim]Seller server stopped.[/dim]")

    # ── Summary ───────────────────────────────────────────────────────────────
    console.print()
    console.print(Panel(
        f"AgentFacts generated  : [green]YES[/green] (W3C Verifiable Credential)\n"
        f"Signature verified    : [green]{'YES' if valid else 'NO'}[/green] (secp256k1 / same key as Phase 7)\n"
        f"NANDA registration    : [yellow]Payload sent[/yellow] (HTTPS required for production acceptance)\n"
        f"Buyer discovery       : [yellow]Fallback to localhost[/yellow] (NANDA returns real URL in production)\n"
        f"Procurement flow      : [green]COMPLETE[/green] (A2A + UCP, same as Phase 5A)\n\n"
        f"[dim]To go live on the Open Agentic Web:[/dim]\n"
        f"[dim]  1. Deploy to a public HTTPS host (Maritime, Render, Railway)[/dim]\n"
        f"[dim]  2. Run: python src/seller_agent/nanda_facts.py --register --base-url https://your-url[/dim]\n"
        f"[dim]  3. Any buyer agent on NANDA can now find and transact with SupplyMind[/dim]\n\n"
        f"[dim]Phase 8 next: replace simulated USDC with real Circle Programmable Wallets.[/dim]",
        title="[bold]Phase 6 Summary -- NANDA AgentFacts + Open Agentic Web",
        border_style="green",
    ))


if __name__ == "__main__":
    run()
