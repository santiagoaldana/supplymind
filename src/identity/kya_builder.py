"""
KYA Document Builder — Phase 7

Generates a cryptographically signed KYA (Know Your Agent) identity document.

KEY STORAGE:
  Private key is stored in .keys/seller_private_key.hex (gitignored).
  If no key exists, a new one is generated automatically.
  Public key and wallet address are derived from the private key each run —
  they never need to be stored separately.

SIGNED FIELDS (everything except 'proof'):
  id, name, version, description, owner, wallet, capabilities, endpoints

PROOF FIELD (added after signing):
  type:        "secp256k1"
  public_key:  hex-encoded uncompressed public key
  wallet:      Ethereum-compatible wallet address derived from public key
  algorithm:   "SHA-256 + ECDSA/secp256k1"
  signature:   hex-encoded DER signature over SHA-256(canonical document)
  signed_at:   ISO 8601 timestamp

Usage:
  python src/identity/kya_builder.py
    → generates keys if needed, signs KYA, writes to well_known/kya.json
    → prints DID, public key, wallet address, and signature for inspection
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.identity.keys import (
    generate_keypair,
    private_key_to_hex,
    private_key_from_hex,
    public_key_to_hex,
    derive_wallet_address,
    sign_document,
    verify_signature,
)

KEYS_DIR      = Path(__file__).parent.parent.parent / ".keys"
KEY_FILE      = KEYS_DIR / "seller_private_key.hex"
KYA_OUT_PATH  = Path(__file__).parent.parent / "seller_agent" / "well_known" / "kya.json"

BASE_URL      = "http://localhost:8080"
SELLER_NAME   = "SupplyMind Seller"


def load_or_create_private_key():
    KEYS_DIR.mkdir(exist_ok=True)
    if KEY_FILE.exists():
        hex_str = KEY_FILE.read_text().strip()
        print(f"  Loaded existing key from {KEY_FILE}")
        return private_key_from_hex(hex_str)
    else:
        private_key, _ = generate_keypair()
        KEY_FILE.write_text(private_key_to_hex(private_key))
        KEY_FILE.chmod(0o600)  # owner read-only
        print(f"  Generated new key, saved to {KEY_FILE}")
        return private_key


def build_signed_kya(
    private_key,
    base_url:     str = BASE_URL,
    seller_name:  str = SELLER_NAME,
) -> dict:
    public_key     = private_key.public_key()
    public_key_hex = public_key_to_hex(public_key)
    wallet_address = derive_wallet_address(public_key)
    did            = f"did:web:{base_url.replace('http://', '').replace('https://', '')}"

    # Build the document body (no proof field yet — signing comes next)
    doc = {
        "@context": [
            "https://schema.org",
            "https://kya.agentprotocol.xyz/v1",
        ],
        "@type": "AgentIdentity",
        "id":      did,
        "name":    seller_name,
        "version": "2.0.0",
        "description": (
            "Autonomous B2B seller agent for office supplies. "
            "Exposes a UCP-compliant product catalog, accepts purchase requests "
            "via A2A and Google UCP protocols, and settles payments via AP2 mandate."
        ),
        "owner": {
            "@type":   "Person",
            "name":    "SupplyMind Operator",
            "role":    "Agent Operator",
            "contact": "supplymind@localhost",
        },
        "wallet": {
            "@type":    "ProgrammableWallet",
            "provider": "Circle",
            "network":  "USDC on Ethereum Sepolia testnet",
            "address":  wallet_address,
            "note":     "Phase 8 replaces this with a real Circle testnet wallet.",
        },
        "capabilities": [
            "ucp:catalog",
            "google-ucp:v2026-04-08",
            "a2a:task/send",
            "a2a:task/get",
            "mcp:inventory",
            "mcp:shipping",
        ],
        "endpoints": {
            "catalog":     f"{base_url}/.well-known/ucp.json",
            "ucp_profile": f"{base_url}/.well-known/ucp",
            "identity":    f"{base_url}/.well-known/kya.json",
            "a2a_tasks":   f"{base_url}/tasks/send",
        },
    }

    # Sign the document (proof field excluded from signed content)
    signature = sign_document(doc, private_key)

    # Add proof field
    doc["proof"] = {
        "type":       "secp256k1",
        "public_key": public_key_hex,
        "wallet":     wallet_address,
        "algorithm":  "SHA-256 + ECDSA/secp256k1",
        "signature":  signature,
        "signed_at":  datetime.now(timezone.utc).isoformat(),
    }

    return doc


def main() -> None:
    print("\nKYA Builder — Phase 7: Real Cryptographic Identity")
    print("=" * 55)

    print("\n[1] Loading or generating secp256k1 key pair...")
    private_key    = load_or_create_private_key()
    public_key     = private_key.public_key()
    public_key_hex = public_key_to_hex(public_key)
    wallet_address = derive_wallet_address(public_key)
    did            = f"did:web:{BASE_URL.replace('http://', '')}"

    print(f"\n[2] Identity derived from key pair:")
    print(f"  DID            : {did}")
    print(f"  Public key     : {public_key_hex[:32]}...{public_key_hex[-8:]}")
    print(f"  Wallet address : {wallet_address}")

    print(f"\n[3] Building and signing KYA document...")
    kya_doc   = build_signed_kya(private_key)
    signature = kya_doc["proof"]["signature"]
    print(f"  Signature      : {signature[:32]}...{signature[-8:]}")
    print(f"  Signed at      : {kya_doc['proof']['signed_at']}")

    print(f"\n[4] Verifying signature...")
    valid = verify_signature(kya_doc, signature, public_key_hex)
    print(f"  Verification   : {'PASSED' if valid else 'FAILED'}")

    if not valid:
        print("  ERROR: signature verification failed. Aborting.")
        sys.exit(1)

    print(f"\n[5] Writing signed KYA to {KYA_OUT_PATH}...")
    KYA_OUT_PATH.write_text(json.dumps(kya_doc, indent=2))
    print(f"  Done.")

    print(f"\n  The buyer agent can now verify this seller's identity")
    print(f"  by fetching /.well-known/kya.json and calling verify_signature().")
    print()


if __name__ == "__main__":
    main()
