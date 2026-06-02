# SupplyMind — CLAUDE.md

## Project Purpose

SupplyMind is a hands-on learning project to deeply understand how AI agents buy, sell, and transact — by building a working multi-agent B2B autonomous commerce system from scratch.

**Owner:** Santiago Aldana — MIT Sloan MBA, 20+ yrs FinTech/AI/payments/LATAM leadership.

**Goal:** Build real, working implementations of MCP, A2A, UCP, AP2, DNSid, and Agentic Payments protocols across 15 phases, with security analysis and protocol reflection at each layer.

## What We're Building

**SupplyMind Marketplace** — a simulated B2B marketplace where a Buyer Agent autonomously sources office supplies from a Seller Agent.

- Buyer discovers seller via A2A
- Queries products via UCP-compliant catalog
- Pays via Agentic Payment Interface
- Both agents use MCP servers to access real tools

## Project Structure

```
SupplyMind/
  CLAUDE.md                        # This file
  requirements.txt
  .env                             # API keys (never commit)
  agentic-commerce-learning-plan.pdf
  Prompts/
    next_phases_prompt.md          # Session prompt for Phases 8-15
  docs/
    protocol_reflection.md         # Full 15-phase protocol + security analysis
  src/
    inventory_server/              # Phase 1: MCP server, SQLite-backed
    shipping_server/               # Phase 1: MCP server, stub responses
    payment_server/                # Phase 4: AP2 mandate engine, dual-rail MPP
    buyer_agent/                   # Phase 3+: Claude as buyer, A2A client
    seller_agent/                  # Phase 3+: FastAPI + Claude, A2A + UCP server
    identity/                      # Phase 7: secp256k1, DID, KYA signing
    governance/                    # Phase 10 (planned): audit dashboard
  data/                            # SQLite DBs, seed data
  logs/                            # Tool call traces, run logs
  tests/                           # Phase test scripts (test_phase1 through test_phase12)
  logs/
    audit.jsonl                    # Durable append-only audit event log (persists across restarts)
```

## 15-Phase Build Plan

| # | Name | Protocols / Frameworks | Status |
|---|------|----------------------|--------|
| 1 | MCP Servers | MCP (Anthropic) | Done |
| 2 | UCP Catalog | UCP (Google), MCP | Done |
| 3 | Agent Discovery + Micro-payment | A2A (Google), x402 | Done |
| 4 | Procurement Loop | AP2, ACF, MPP | Done |
| 5 | Protocol Reflection + Second Seller | A2A, UCP | Partial |
| 6 | NANDA Discovery | NANDA, W3C VC | Done |
| 7 | Cryptographic Identity | secp256k1, DID, KYA | Done |
| 8 | DNSid Ownership Layer | DNSid, PKI, DNS | Done |
| 9 | AP2 v0.2.0 Mandate Upgrade | AP2 v0.2.0, secp256k1 | Done |
| 10 | Seller Authorization Manifest | secp256k1, AP2 pattern, DNSid | Done |
| 11 | Governance Dashboard | DNSid, AP2, x402, NANDA | Done |
| 12 | Multi-Protocol Checkout | ACP (OpenAI/Stripe), UCP | Done |
| 13 | Agent Wallet Layer | Stripe Link, Coinbase/Base MCP | Planned |
| 14 | Network Credential Layer | Visa TAP, Mastercard Agent Pay | Planned |
| 15 | Fraud and Bot Detection | Stripe Radar, DNSid rate limiting | Planned |
| 16 | Stablecoin Settlement | x402 (LF), AWS AgentCore, USDC/Base | Planned |

**Current phase:** Phase 13 (Agent Wallet Layer)

## Key Protocols

- **MCP:** Anthropic / Linux Foundation. Tools, resources, prompts. stdio or SSE transport.
- **UCP:** Google + Shopify/Walmart coalition. Machine-readable product catalogs, checkout journey. google-ucp:v2026-04-08.
- **A2A:** Google DeepMind / Linux Foundation. Agent Cards, task lifecycle (POST /tasks/send, GET /tasks/{id}).
- **x402:** Coinbase / Linux Foundation. HTTP 402 pay-per-request micro-payment protocol. USDC on Base.
- **AP2:** Google. Spending Mandate engine, tiered autonomy (ACF), Human Not Present payments (v0.2.0).
- **NANDA:** Project NANDA. Decentralized agent registry, W3C Verifiable Credentials.
- **DNSid:** Identity Digital Innovation Labs. DNS-anchored agent ownership registry, revocation.
- **ACP:** OpenAI + Stripe. Agentic Commerce Protocol, B2C/B2B checkout.
- **Visa TAP:** Visa. Trusted Agent Protocol, RFC 9421, cryptographic agent credential.
- **Mastercard Agent Pay:** Mastercard. Agentic Tokens, Verifiable Intent, network-level agent authorization.

## Code Conventions

- Language: Python 3.11+
- MCP SDK: `mcp` (Anthropic's official Python MCP SDK)
- Claude SDK: `anthropic`
- Web framework (Phase 3+): `fastapi` + `uvicorn`
- DB: `sqlite3` (stdlib)
- Env vars via `python-dotenv`
- No comments explaining what code does. Comments only for non-obvious constraints or workarounds.
- No em dashes, en dashes, or hyphens in any written output (docs, logs, posts).

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | All Claude API calls |

Set in `.env` file (never commit).

## Security Analysis

Every phase in SupplyMind has an associated security analysis in
`docs/protocol_reflection.md`. Each protocol entry covers:
- Security loopholes tagged by Clerk's four auth questions (Identity, Scoping,
  Approvals, Enforcement)
- Alternatives considered and why the chosen protocol was selected
- Dependencies and sequencing: what breaks if this phase is skipped
- Maturity rating: production stable / maturing / experimental

When completing a phase, update `docs/protocol_reflection.md` with any
findings that deviate from the planned analysis.

## Models

- `claude-opus-4-6` for agent reasoning tasks
- `claude-haiku-4-5-20251001` for classification or lightweight tool calls
