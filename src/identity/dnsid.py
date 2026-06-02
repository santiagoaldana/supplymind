"""
DNSid Agent Ownership Layer — Phase 8

PROTOCOL: DNSid (Identity Digital Innovation Labs, launched April 27 2026)

DNSid anchors AI agent ownership to a DNS domain and blockchain record.
It is the "birth certificate" layer for agents: register, resolve, revoke.

HOW IT RELATES TO PHASE 7 (secp256k1 / DID):
  Phase 7 answers: does this key belong to who claims it?
  DNSid answers: does this domain own this agent, and has that ownership changed?

  Phase 7 alone has no revocation. If a private key is compromised, there is
  no mechanism to invalidate it. DNSid adds the revocation layer: once an
  agent handle is revoked, all counterparties see it immediately.

HANDLE FORMAT:
  dnsid://<domain>/agents/<agent-id>
  Example: dnsid://supplymind.localhost/agents/seller-001

MOCK vs PRODUCTION:
  This module uses an in-memory registry (same pattern as MANDATES in mandate.py).
  In production DNSid would write a DNS TXT record and a blockchain entry.
  The interface is identical — swap the storage backend, not the calling code.

SPECIAL TEST HANDLE:
  dnsid://test.invalid/revoked  — always returns revoked (for gate testing)
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from src.governance.event_log import log_event

_REGISTRY: dict[str, dict] = {}

_TEST_REVOKED_HANDLE = "dnsid://test.invalid/revoked"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def register_agent(
    agent_id:       str,
    owner:          str,
    domain:         str,
    public_key_hex: Optional[str] = None,
) -> str:
    """
    Register an agent in the DNSid registry.

    In production this would:
      1. Verify domain ownership via DNS challenge
      2. Write a TXT record: _agent.<domain> -> <handle>
      3. Anchor the entry on-chain for tamper evidence

    Returns the dnsid handle: dnsid://<domain>/agents/<agent_id>
    """
    handle = f"dnsid://{domain}/agents/{agent_id}"
    _REGISTRY[handle] = {
        "handle":         handle,
        "agent_id":       agent_id,
        "owner":          owner,
        "domain":         domain,
        "public_key_hex": public_key_hex,
        "status":         "active",
        "created_at":     _now(),
        "revoked_at":     None,
        "revocation_reason": None,
        "registration_id": str(uuid.uuid4()),
    }
    log_event("Identity", "agent_registered", handle, owner, f"agent_id={agent_id} domain={domain}")
    return handle


def resolve_dnsid(handle: str) -> dict:
    """
    Resolve a DNSid handle to its registration record.

    Returns the full record if found.
    Returns {"status": "not_found"} if the handle is unknown.

    The test handle dnsid://test.invalid/revoked always returns revoked
    so gate logic can be tested without performing a real revocation.
    """
    if handle == _TEST_REVOKED_HANDLE:
        return {
            "handle":   handle,
            "status":   "revoked",
            "owner":    "test",
            "domain":   "test.invalid",
            "agent_id": "revoked",
            "created_at":  _now(),
            "revoked_at":  _now(),
            "revocation_reason": "test-sentinel",
        }

    record = _REGISTRY.get(handle)
    if not record:
        return {"status": "not_found", "handle": handle}
    return dict(record)


def revoke_agent(handle: str, reason: str = "revoked by owner") -> dict:
    """
    Revoke an agent's DNSid registration.

    In production this would update the DNS TXT record and write a revocation
    transaction on-chain. Once revoked, any resolve call returns status=revoked
    and all counterparty gates that check DNSid will reject the agent.

    Returns the updated record or an error dict.
    """
    record = _REGISTRY.get(handle)
    if not record:
        return {"error": f"Handle {handle} not found"}
    if record["status"] == "revoked":
        return {"error": f"Handle {handle} is already revoked"}

    record["status"]             = "revoked"
    record["revoked_at"]         = _now()
    record["revocation_reason"]  = reason
    log_event("Identity", "agent_revoked", handle, record["owner"], f"reason={reason}")
    return dict(record)


def list_registry() -> list[dict]:
    """
    Return all registered handles.
    Used by the Phase 10 Governance Dashboard to display the agent registry.
    """
    return [dict(r) for r in _REGISTRY.values()]
