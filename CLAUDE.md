# SupplyMind — CLAUDE.md

## Communication Style

- Be direct and critical. Polite confrontation is expected and valued.
- When something is wrong, incomplete, or a weak argument, say so clearly
  and explain why. Do not soften the point into uselessness.
- Do not validate ideas just because the user proposed them. If the logic
  has a hole, name the hole.
- Agreements should be earned. Never open with praise of the question or idea.
- Never say "honest opinion," "honest answer," "honest assessment," or any
  variant. Honesty is the baseline, not a special state worth announcing.
- When the user asks a question that has a better version of itself, ask
  the better question back before answering the original one.
- Short, direct responses are preferred over long, padded ones.

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
    cart_server/                   # Phase 12.5: Universal Cart, SQLite-backed
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
| 5 | Protocol Reflection + Second Seller | A2A, UCP | Done |
| 6 | Cryptographic Identity | secp256k1, DID, KYA | Done |
| 7 | NANDA Discovery | NANDA, W3C VC | Done |
| 8 | DNSid Ownership Layer | DNSid, PKI, DNS | Done |
| 9 | AP2 v0.2.0 Mandate Upgrade | AP2 v0.2.0, secp256k1 | Done |
| 10 | Seller Authorization Manifest | secp256k1, AP2 pattern, DNSid | Done |
| 11 | Governance Dashboard | DNSid, AP2, x402, NANDA | Done |
| 12 | Multi-Protocol Checkout | ACP (OpenAI/Stripe), UCP | Done |
| 12.5 | Universal Cart | Google Universal Cart | Done |
| 13 | Agent Wallet Layer | Stripe Link, Coinbase/Base MCP | Done (13a mock; 13b optional) |
| 14 | Network Credential Layer | Visa TAP, Mastercard Agent Pay | Done |
| 15 | Fraud and Bot Detection | Sardine, DNSid rate limiting | Planned |
| 16 | Open Agent Micropayments | x402, USDC/Base, on-chain credentials (Base testnet) | Planned |
| 17 | Production Agent Infrastructure | AWS AgentCore, Google Agent Engine, Azure AI Foundry, Cloudflare Workers AI, OpenClaw (self-hosted) | Planned |

**Current phase:** Phase 15 (Fraud and Bot Detection)

## Prototype Reminders

- **Phase 16 AP4M pattern (added June 15 2026):** Mastercard AP4M (launched June 10 2026) introduces a transaction model not yet in SupplyMind: AI agents making sub-cent payments per request with no human in the loop (API call fees, per-query data licensing, compute billing). Phase 16 replicates this as an open protocol: x402 per-request pricing on seller endpoints, buyer agent continuous payment loop, secp256k1 credentials anchored on Base testnet (public registry contract), USDC settlement. This is architecturally equivalent to AP4M but permissionless: no Mastercard enrollment, no network liability guarantee, bilateral trust via on-chain verification. The missing element vs AP4M is not technical but commercial: Mastercard's fraud coverage and chargeback system.
- **Phase 17 infrastructure comparison (added June 15 2026):** Evaluate production agent hosting options against SupplyMind's actual requirements (MCP tool access, A2A discovery, x402 payment headers, secp256k1 signing). OpenClaw is the highest-compatibility option: open-source, self-hosted, A2A v0.3.0 and MCP native, 347k GitHub stars as of April 2026. Compare against managed cloud options (AWS AgentCore, Google Agent Engine, Azure AI Foundry, Cloudflare Workers AI) on protocol fit, data sovereignty, cost, and operational complexity. Do this phase last so evaluation criteria are grounded in what the full stack actually needs.

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
- **AP4M:** Mastercard. Agent Pay for Machines (launched June 10 2026). Second-generation agentic payments for machine-to-machine transactions with no human in the loop. Four layers: Credentialing (on-chain: Polygon, Solana, Base), Permissioning (Agentic Tokens + Verifiable Intent), Transacting (card + bank rails, machine speed), Settling (fiat + USDC, RLUSD, PYUSD). Sub-cent micropayments at high frequency. 31 crypto-native partners including Coinbase, Ripple, Stripe, Cloudflare. Phase 16 replicates this pattern as an open protocol via x402 + Base testnet.
- **OpenClaw:** Open-source self-hosted AI agent framework. A2A v0.3.0 and MCP native. 347k GitHub stars as of April 2026. Local-first runtime with persistent memory, sandboxed execution, cryptographic skill verification. Evaluated in Phase 17 as the highest protocol-compatibility hosting option for SupplyMind.
- **Visa ICC:** Visa Intelligent Commerce Connect. Single merchant endpoint routing between TAP, MPP, ACP, and UCP simultaneously. Announced April 8, 2026. Technically equivalent to Firmly Connect at the protocol translation layer. Does not touch identity, mandate signing, or settlement. Strategic implication: ICC commoditizes the protocol aggregation layer, making Firmly Connect's neutrality the only remaining differentiator at that layer. The identity layer (Firmly ID, DNSid, LoginID) is the moat ICC cannot replicate.
- **Firmly Connect:** Firmly. No-code merchant onboarding platform abstracting MCP, AP2, ACP, UCP, A2A, KYA, TAP. Launched March 2026. Live: Best Buy, Backcountry. Network-neutral alternative to ICC. Does not yet include the identity layer (Firmly ID, DNSid, LoginID mandate attestation) which is the proposed extension.
- **Firmly + LoginID Identity Stack (proposed):** Firmly Connect (protocol translation) plus identity layer: Firmly ID subdomain registry for humans, DNSid anchor for businesses, LoginID FIDO2 passkey binding for mandate attestation, AP2 v0.2.0 signed mandates, Seller Authorization Manifest. SupplyMind is the working prototype proving this stack is implementable. This is what differentiates the combined Firmly + LoginID stack from both ICC and Firmly Connect alone.
- **Visa + OpenAI Agent Payments:** Visa. "Visa Partners with OpenAI to Power the Next Generation of AI Commerce," announced June 10 2026 at Visa Payments Forum (newsroom releaseId 22496). Part of the broader Visa Intelligent Commerce initiative (partner ecosystem named: Microsoft, IBM, Anthropic, Samsung, Stripe). Visa payment capabilities integrated into OpenAI experiences so agents can shop and pay across the roughly 175 million Visa merchant locations once the user grants permission. Mechanism: tokenized Visa credentials, real time authorization, fraud monitoring. Transactions run within explicit user controls: spending limits, merchant categories, required approvals. Those controls are a real world parallel to SupplyMind AP2 mandate scoping. Production instance of the Phase 14 network credential layer and the Phase 13 wallet layer. Replaces OpenAI Instant Checkout (fee based, retired March 2026). No launch date or pricing yet.
- **Visa Agentic Directory:** Visa. Announced June 10 2026 at Visa Payments Forum (newsroom releaseId 22491, "AI, Stablecoin and Token Innovations"). Visa verified registry of legitimate agents and merchants enabling mutual trust before transacting. Centralized incumbent counterpart to SupplyMind decentralized discovery (NANDA Phase 7, DNSid Phase 8). Competes directly at the discovery layer CLAUDE.md frames as a moat.
- **Visa Agent Score:** Visa, built with New Generation. Announced June 10 2026 at Visa Payments Forum (newsroom releaseId 22491). Merchant tool that scores whether a website is navigable and transactable by AI agents. Seller side mirror of the UCP catalog readiness concept.

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
