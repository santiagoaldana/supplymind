"""
NANDA AgentFacts Generator -- Phase 6

Generates a W3C Verifiable Credential (JSON-LD) AgentFacts document for
registration on the NANDA NEST decentralized agent registry.

WHAT THIS DOES:
  Builds an AgentFacts document by combining:
    - Our DID from the existing signed KYA (did:web:localhost:8080)
    - Our capabilities, remapped to NANDA's URN format
    - Our secp256k1 signature from Phase 7

  Then optionally POSTs it to https://nest.projectnanda.org/api/network/register

WHY NANDA:
  NANDA is a decentralized registry (like DNS, but for agents). Once registered,
  any buyer agent anywhere can search NANDA and find SupplyMind without knowing
  our URL in advance. This is the "Open Agentic Web" step.

NANDA vs HTTPS CONSTRAINT:
  NANDA production requires an HTTPS endpoint. We are on localhost (HTTP).
  So --register will show the payload it WOULD send, and attempt the POST.
  If NANDA rejects localhost, we print the rejection reason and move on.
  This is the expected behavior for a local development environment.

CAPABILITY MAPPING (our KYA -> NANDA URN format):
  "ucp:catalog"               -> "urn:nanda:cap:ucp:catalog"
  "google-ucp:v2026-04-08"   -> "urn:nanda:cap:google-ucp:v2026-04-08"
  "a2a:task/send"             -> "urn:nanda:cap:a2a:task:send"
  "a2a:task/get"              -> "urn:nanda:cap:a2a:task:get"
  "mcp:inventory"             -> "urn:nanda:cap:mcp:inventory"
  "mcp:shipping"              -> "urn:nanda:cap:mcp:shipping"

Usage:
  python src/seller_agent/nanda_facts.py --preview    # print AgentFacts JSON
  python src/seller_agent/nanda_facts.py --register   # attempt NANDA registration
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx

from src.identity.keys import (
    load_or_create_private_key_from_file,
    public_key_to_hex,
    derive_wallet_address,
    sign_document,
)

KYA_PATH      = Path(__file__).parent / "well_known" / "kya.json"
NANDA_API_URL = "https://nest.projectnanda.org/api/network/register"
BASE_URL      = "http://localhost:8080"
SELLER_NAME   = "SupplyMind Seller"

CAPABILITY_MAP = {
    "ucp:catalog":             "urn:nanda:cap:ucp:catalog",
    "google-ucp:v2026-04-08": "urn:nanda:cap:google-ucp:v2026-04-08",
    "a2a:task/send":           "urn:nanda:cap:a2a:task:send",
    "a2a:task/get":            "urn:nanda:cap:a2a:task:get",
    "mcp:inventory":           "urn:nanda:cap:mcp:inventory",
    "mcp:shipping":            "urn:nanda:cap:mcp:shipping",
}


def _load_kya() -> dict:
    if not KYA_PATH.exists():
        print(f"  ERROR: KYA not found at {KYA_PATH}")
        print(f"  Run: python src/identity/kya_builder.py")
        sys.exit(1)
    return json.loads(KYA_PATH.read_text())


def build_agent_facts(private_key, base_url: str = BASE_URL) -> dict:
    """
    Build a NANDA-compatible AgentFacts document (W3C Verifiable Credential).

    Structure follows W3C VC v2 with NANDA extensions:
      @context        -> JSON-LD contexts (W3C VC + NANDA)
      type            -> ["VerifiableCredential", "AgentFacts"]
      id              -> our DID
      issuer          -> same DID (self-issued credential)
      issuanceDate    -> now (ISO 8601)
      credentialSubject -> agent capabilities, endpoints, operator
      proof           -> secp256k1 signature (same key as KYA)
    """
    kya = _load_kya()
    public_key     = private_key.public_key()
    public_key_hex = public_key_to_hex(public_key)
    wallet_address = derive_wallet_address(public_key)
    did            = kya.get("id", f"did:web:{base_url.replace('http://', '')}")

    kya_caps = kya.get("capabilities", [])
    nanda_caps = [CAPABILITY_MAP.get(c, f"urn:nanda:cap:{c.replace('/', ':')}") for c in kya_caps]

    doc = {
        "@context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://projectnanda.org/contexts/agentfacts/v1",
        ],
        "type": ["VerifiableCredential", "AgentFacts"],
        "id":   did,
        "issuer": did,
        "issuanceDate": datetime.now(timezone.utc).isoformat(),
        "credentialSubject": {
            "id":          did,
            "name":        kya.get("name", SELLER_NAME),
            "description": kya.get("description", ""),
            "endpoint":    base_url,
            "capabilities": nanda_caps,
            "endpoints": {
                "agent_card":  f"{base_url}/.well-known/agent-card.json",
                "kya":         f"{base_url}/.well-known/kya.json",
                "catalog":     f"{base_url}/.well-known/ucp.json",
                "ucp_profile": f"{base_url}/.well-known/ucp",
                "tasks":       f"{base_url}/tasks/send",
                "checkout":    f"{base_url}/ucp/v1/checkout-sessions",
            },
            "auth": {
                "method":        "secp256k1",
                "public_key":    public_key_hex,
                "wallet_address": wallet_address,
            },
            "tags": ["b2b", "procurement", "office-supplies", "ucp", "a2a"],
            "operator": kya.get("owner", {}),
        },
    }

    signature = sign_document(doc, private_key)

    doc["proof"] = {
        "type":               "secp256k1Signature2020",
        "created":            datetime.now(timezone.utc).isoformat(),
        "verificationMethod": f"{did}#key-1",
        "proofPurpose":       "assertionMethod",
        "public_key":         public_key_hex,
        "signature":          signature,
    }

    return doc


def preview(agent_facts: dict) -> None:
    print("\nAgentFacts Document (W3C Verifiable Credential)")
    print("=" * 60)
    print()

    cs = agent_facts["credentialSubject"]
    print(f"  DID / Issuer     : {agent_facts['id']}")
    print(f"  Issued at        : {agent_facts['issuanceDate']}")
    print(f"  Agent name       : {cs['name']}")
    print(f"  Endpoint         : {cs['endpoint']}")
    print()
    print(f"  Capabilities ({len(cs['capabilities'])}):")
    for cap in cs["capabilities"]:
        print(f"    {cap}")
    print()
    print(f"  Tags             : {cs['tags']}")
    print()
    print(f"  Auth method      : {cs['auth']['method']}")
    print(f"  Public key       : {cs['auth']['public_key'][:24]}...{cs['auth']['public_key'][-8:]}")
    print(f"  Wallet address   : {cs['auth']['wallet_address']}")
    print()
    sig = agent_facts["proof"]["signature"]
    print(f"  Proof type       : {agent_facts['proof']['type']}")
    print(f"  Signature        : {sig[:32]}...{sig[-8:]}")
    print()
    print("  Full JSON:")
    print(json.dumps(agent_facts, indent=2))


def register(agent_facts: dict) -> None:
    """
    POST the AgentFacts to NANDA NEST.

    NANDA also accepts a simpler flat registration payload (non-VC format)
    via /api/network/register. We send both: the full VC as agentfacts,
    and the flat fields NANDA expects at the top level.
    """
    cs = agent_facts["credentialSubject"]

    payload = {
        "name":         cs["name"],
        "description":  cs["description"],
        "endpoint":     cs["endpoint"],
        "tags":         cs["tags"],
        "capabilities": cs["capabilities"],
        "did":          agent_facts["id"],
        "agentfacts":   agent_facts,
    }

    print(f"\n  Attempting NANDA registration...")
    print(f"  POST {NANDA_API_URL}")
    print(f"  Endpoint in payload: {payload['endpoint']}")
    print()
    print("  NOTE: NANDA production requires HTTPS endpoints.")
    print("  localhost HTTP endpoints are expected to be rejected.")
    print("  This run shows the complete registration flow.")
    print()

    try:
        r = httpx.post(NANDA_API_URL, json=payload, timeout=10.0)
        print(f"  HTTP status      : {r.status_code}")
        try:
            body = r.json()
            print(f"  Response         : {json.dumps(body, indent=4)}")
        except Exception:
            print(f"  Response text    : {r.text[:500]}")

        if r.status_code in (200, 201):
            print()
            print("  SUCCESS: SupplyMind is now registered on NANDA NEST.")
            print("  Search at https://nest.projectnanda.org to verify.")
        else:
            print()
            print("  Registration was not accepted (expected for localhost).")
            print("  Deploy to a public HTTPS host to complete production registration.")

    except httpx.ConnectError:
        print("  Could not reach NANDA NEST (network error).")
        print("  Check connectivity or try again later.")
    except Exception as e:
        print(f"  Unexpected error: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="NANDA AgentFacts Generator")
    parser.add_argument("--preview",  action="store_true", help="Print AgentFacts JSON")
    parser.add_argument("--register", action="store_true", help="POST to NANDA NEST")
    parser.add_argument("--base-url", default=BASE_URL,    help="Agent base URL")
    args = parser.parse_args()

    if not args.preview and not args.register:
        args.preview = True

    print("\nNANDA AgentFacts Generator -- Phase 6")
    print("=" * 55)

    print("\n[1] Loading secp256k1 private key...")
    keys_dir = Path(__file__).parent.parent.parent / ".keys"
    key_file  = keys_dir / "seller_private_key.hex"
    private_key = load_or_create_private_key_from_file(key_file)

    print("\n[2] Building AgentFacts document...")
    agent_facts = build_agent_facts(private_key, base_url=args.base_url)
    print(f"  DID              : {agent_facts['id']}")
    print(f"  Capabilities     : {len(agent_facts['credentialSubject']['capabilities'])}")
    sig = agent_facts["proof"]["signature"]
    print(f"  Signature        : {sig[:32]}...{sig[-8:]}")

    if args.preview:
        preview(agent_facts)

    if args.register:
        register(agent_facts)

    print()


if __name__ == "__main__":
    main()
