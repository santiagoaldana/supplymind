"""
DNSid Registry Seed — Phase 8

Registers the three SupplyMind agents at startup.
Run this directly to verify registration, or import seed() and call it
before any flow that depends on DNSid resolution.

Usage:
  python src/identity/dnsid_registry_seed.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.identity.dnsid import register_agent, resolve_dnsid

AGENTS = [
    {
        "agent_id": "inventory-001",
        "owner":    "supplymind.localhost",
        "domain":   "supplymind.localhost",
    },
    {
        "agent_id": "procurement-001",
        "owner":    "supplymind.localhost",
        "domain":   "supplymind.localhost",
    },
    {
        "agent_id": "seller-001",
        "owner":    "supplymind.localhost",
        "domain":   "supplymind.localhost",
    },
]


def seed() -> dict[str, str]:
    """Register all SupplyMind agents. Returns {agent_id: handle}."""
    handles = {}
    for agent in AGENTS:
        handle = register_agent(
            agent_id=agent["agent_id"],
            owner=agent["owner"],
            domain=agent["domain"],
        )
        handles[agent["agent_id"]] = handle
    return handles


if __name__ == "__main__":
    handles = seed()
    print("DNSid registry seeded:")
    for agent_id, handle in handles.items():
        record = resolve_dnsid(handle)
        print(f"  {handle}")
        print(f"    owner:      {record['owner']}")
        print(f"    status:     {record['status']}")
        print(f"    created_at: {record['created_at']}")
        print()
