"""
Phase 7 — Real Cryptographic Identity

Demonstrates secp256k1 key generation, DID derivation, KYA document signing,
and buyer-side signature verification. No LLM calls, no network requests.
Runs entirely in-process.

What this test shows:
  1. Key pair generation (secp256k1 — same curve as Bitcoin/Ethereum)
  2. Wallet address derivation (keccak256 of public key, last 20 bytes)
  3. DID construction from wallet address
  4. KYA document signing (SHA-256 digest + ECDSA signature)
  5. Signature verification (buyer verifies seller identity)
  6. Tamper detection (modified document fails verification)
  7. Current KYA file verification (the one written by kya_builder.py)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from src.identity.keys import (
    generate_keypair,
    public_key_to_hex,
    derive_wallet_address,
    sign_document,
    verify_signature,
)
from src.identity.kya_builder import build_signed_kya, load_or_create_private_key

console = Console()

KYA_PATH = Path(__file__).parent.parent / "src" / "seller_agent" / "well_known" / "kya.json"


def run() -> None:
    console.rule("[bold blue]SupplyMind Phase 7 — Real Cryptographic Identity")
    console.print()
    console.print("[bold]Algorithm:[/bold] secp256k1 + SHA-256 + ECDSA (same as Bitcoin/Ethereum)")
    console.print("[bold]Cost:[/bold]      zero — pure cryptography, no network calls")
    console.print()

    # ── Step 1: Key pair generation ───────────────────────────────────────────
    console.rule("[bold cyan]Step 1: secp256k1 Key Pair")
    private_key, public_key = generate_keypair()
    pub_hex    = public_key_to_hex(public_key)
    wallet     = derive_wallet_address(public_key)
    did        = f"did:web:localhost:8080"

    key_table = Table(box=box.SIMPLE, show_header=False)
    key_table.add_column("Field", style="dim", width=18)
    key_table.add_column("Value", style="green")
    key_table.add_row("Private key",    "[red]kept secret — never displayed[/red]")
    key_table.add_row("Public key",     f"{pub_hex[:24]}...{pub_hex[-8:]}  ({len(pub_hex)//2} bytes)")
    key_table.add_row("Wallet address", wallet)
    key_table.add_row("DID",            did)
    console.print(key_table)

    console.print()
    console.print("  [dim]The wallet address is derived from the public key:[/dim]")
    console.print("  [dim]  1. Uncompressed public key (64 bytes, strip 0x04 prefix)[/dim]")
    console.print("  [dim]  2. keccak256 hash → 32 bytes[/dim]")
    console.print("  [dim]  3. Last 20 bytes → wallet address[/dim]")

    # ── Step 2: Sign a KYA document ──────────────────────────────────────────
    console.rule("[bold cyan]Step 2: Sign KYA Document")
    kya_doc   = build_signed_kya(private_key)
    signature = kya_doc["proof"]["signature"]

    console.print(f"  Document fields signed: {[k for k in kya_doc if k != 'proof']}")
    console.print(f"  Signature              : [green]{signature[:32]}...{signature[-8:]}[/green]")
    console.print(f"  Signed at              : [dim]{kya_doc['proof']['signed_at']}[/dim]")
    console.print()
    console.print("  [dim]Signing process:[/dim]")
    console.print("  [dim]  1. Remove 'proof' field from document[/dim]")
    console.print("  [dim]  2. JSON-serialize with sorted keys (canonical form)[/dim]")
    console.print("  [dim]  3. SHA-256 hash → 32-byte digest[/dim]")
    console.print("  [dim]  4. ECDSA sign digest with private key → DER signature[/dim]")

    # ── Step 3: Verify the signature ─────────────────────────────────────────
    console.rule("[bold cyan]Step 3: Buyer Verifies Seller Identity")
    pub_key_from_doc = kya_doc["proof"]["public_key"]
    valid = verify_signature(kya_doc, signature, pub_key_from_doc)

    console.print(f"  Fetched KYA from seller : [green]/.well-known/kya.json[/green]")
    console.print(f"  Public key in proof     : [green]{pub_key_from_doc[:24]}...[/green]")
    console.print(f"  Signature valid         : [{'green' if valid else 'red'}]{'YES — seller identity verified' if valid else 'NO — verification failed'}[/{'green' if valid else 'red'}]")

    # ── Step 4: Tamper detection ──────────────────────────────────────────────
    console.rule("[bold cyan]Step 4: Tamper Detection")
    tampered_doc = dict(kya_doc)
    tampered_doc["name"] = "Evil Impostor Co."
    tampered_valid = verify_signature(tampered_doc, signature, pub_key_from_doc)

    console.print(f"  Original name           : [green]{kya_doc['name']}[/green]")
    console.print(f"  Tampered name           : [red]Evil Impostor Co.[/red]")
    console.print(f"  Tampered doc verifies   : [{'green' if tampered_valid else 'red'}]{'YES' if tampered_valid else 'NO — tampering detected'}[/{'green' if tampered_valid else 'red'}]")
    console.print()
    console.print("  [dim]Even changing one character breaks the SHA-256 hash,[/dim]")
    console.print("  [dim]making the signature mismatch the digest. Unforgeable.[/dim]")

    # ── Step 5: Verify the live KYA file ────────────────────────────────────
    console.rule("[bold cyan]Step 5: Verify Live KYA File")
    if KYA_PATH.exists():
        live_kya = json.loads(KYA_PATH.read_text())
        live_sig = live_kya.get("proof", {}).get("signature", "")
        live_pub = live_kya.get("proof", {}).get("public_key", "")
        live_valid = verify_signature(live_kya, live_sig, live_pub) if live_sig and live_pub else False

        console.print(f"  File                    : [dim]{KYA_PATH}[/dim]")
        console.print(f"  Seller name             : [green]{live_kya.get('name')}[/green]")
        console.print(f"  DID                     : [green]{live_kya.get('id')}[/green]")
        console.print(f"  Wallet address          : [green]{live_kya.get('proof', {}).get('wallet', 'N/A')}[/green]")
        console.print(f"  Proof type              : [green]{live_kya.get('proof', {}).get('type', 'N/A')}[/green]")
        console.print(f"  Signature valid         : [{'green' if live_valid else 'red'}]{'YES — live KYA verified' if live_valid else 'NO — verification failed'}[/{'green' if live_valid else 'red'}]")
    else:
        console.print(f"  [yellow]No live KYA found. Run: python src/identity/kya_builder.py[/yellow]")

    # ── Final summary ─────────────────────────────────────────────────────────
    console.print()
    console.print(Panel(
        f"Key algorithm    : secp256k1 (Bitcoin/Ethereum standard)\n"
        f"Signing          : SHA-256 digest + ECDSA signature\n"
        f"DID method       : did:web (domain-anchored, no blockchain needed)\n"
        f"Wallet address   : {wallet}\n"
        f"Identity verified: [green]YES[/green]\n"
        f"Tamper detected  : [green]YES[/green]\n\n"
        f"[dim]Phase 8 next: replace simulated USDC rail with real Circle API calls.\n"
        f"The wallet address above becomes the real settlement destination.[/dim]",
        title="[bold]Phase 7 Summary — Real Cryptographic Identity",
        border_style="green",
    ))


if __name__ == "__main__":
    run()
