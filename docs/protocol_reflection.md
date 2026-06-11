# SupplyMind Protocol Reflection

**Author:** Santiago Aldana
**Project:** SupplyMind — a hands-on multi-agent B2B autonomous commerce prototype
**Date:** May 2026

This document reflects on each protocol and framework used in SupplyMind across
all 15 phases: what problem it solves, how we used or plan to use it, what
alternatives existed, what dependencies the phase creates, how mature the
protocol is, the security and trust loopholes it introduces or leaves open,
and why it matters for enterprise agentic commerce.

---

## Protocols vs. Frameworks

A **protocol** is a precise, machine-enforceable specification. Both sides must
implement it exactly or communication fails. It defines what messages look like
and what must happen at the wire level.

A **framework** is a set of principles, recommended practices, and architectural
patterns. It guides how you think about and structure a problem but allows
implementation flexibility. Deviating from a framework does not break the system.

Some entries sit in between: they have a formal spec (protocol-like) but also
governance guidance (framework-like). The classification reflects the dominant intent.

---

## The Four Questions of Agentic Auth (Clerk, May 2026)

Clerk's analysis of agentic authentication identifies four questions that any
agentic system must answer. These are not a framework or protocol — they are an
evaluative lens. Every security loophole in this document is tagged to the
question it most directly undermines.

**1. Identity** — who is the agent, and who does it represent?

**2. Scoping** — what is the agent allowed to do, and how is it constrained?

**3. Approvals** — who approves what the agent is about to do, who vouches for it, and how?

**4. Enforcement** — how do we ensure the agent does only what was approved,
in real time?

Clerk also identifies three keys to agent proliferation: task specification,
approval mechanism, and enforcement engine. Current approaches for each include
AgentPass (Clerk), Mission-bound OAuth (Karl McGuinness), AAuth (Dick Hardt),
MCP (Model Context Protocol) Auth (Linux Foundation), and XAA + ID-JAG (Okta).

**How SupplyMind answers each question across all 15 phases:**

| Question | SupplyMind Answer | Phases | Status |
|----------|------------------|--------|--------|
| Identity | secp256k1 + KYA (Know Your Agent) + DID (Decentralized Identifier) + DNSid (Domain Name System identity) | 7, 8 | Partial (Phase 8 planned) |
| Scoping | AP2 (Agentic Payment Protocol) Mandate constraints + ACF (Agentic Commerce Framework) tiers | 4, 9 | Partial (Phase 9 planned) |
| Approvals | Signed Intent Mandate (secp256k1 in prototype; LoginID FIDO2 biometric in production) | 9 | Planned |
| Enforcement | check_mandate() + DNSid gate | 4, 8 | Partial, gap remains |

A recurring loophole across this entire stack: **possession of a key proves
nothing about ownership or intent.** A stolen private key looks identical to a
legitimate one. This is why DNSid (Phase 8), AP2 Mandates (Phase 9), and
Verifiable Intent (Phase 14) exist as separate layers on top of cryptographic
identity. Cryptography proves the message was signed by a key. Ownership
registries prove who controls the key. Mandates prove what the key is authorized
to do. All three are required for enterprise trust.

---

## Phase 1: MCP — Model Context Protocol

**Type:** Protocol
**Established by:** Anthropic (November 2024). Donated to Linux Foundation
Agentic AI Foundation December 2025. Now Apache 2.0, with OpenAI, Google,
Microsoft, AWS, and Block as founding members.
**Adoption:** Dominant. 9,400+ public servers by April 2026. 78% of enterprise
AI teams report at least one MCP-backed agent in production.
**Maturity:** Production stable. LF (Linux Foundation)-governed, versioned spec, multi-vendor
implementation, wide enterprise adoption.

**Problem it solves:**
AI agents are powerful reasoners but have no built-in way to access external
tools: databases, APIs, shipping calculators. MCP defines a standard interface
so any agent can call any tool without custom wiring per model.

**How we used it:**
Inventory Server (SQLite-backed, 15 products) and Shipping Server (stub cost
estimator), both built with FastMCP. The Phase 4 Payment Server also exposes
all payment tools over MCP so the buyer agent can create mandates, check ACF (Agentic Commerce Framework)
decisions, and execute payments as standard tool calls.

**Dependencies and sequencing:**
MCP is the foundation. Every other phase assumes MCP servers exist for inventory,
shipping, and payment tools. Building any agent capability before MCP servers
are in place means rebuilding the tool interface later. Nothing breaks upstream
if MCP is skipped, but every downstream phase loses its tool access layer.

**Alternatives considered:**
- OpenAI function calling and LangChain tools were the pre-standard predecessors.
  Both require custom wiring per model and per tool — MCP's key advantage is
  model-agnosticism. A Claude-based buyer and a Gemini-based seller can call the
  same MCP tool server without modification.
- Direct REST APIs with no standard interface remain an option for single-vendor
  deployments but create lock-in and require reimplementation for each new model.
- MCP (Model Context Protocol) was the learning target for this phase. MCP is the Linux Foundation standard and the only tool interface layer with multi-vendor production adoption at the time of implementation.

**Security loopholes:**

- [Identity] No tool-level authorization. MCP defines how to call tools, not
  who is allowed to call them. Any agent that can reach the MCP server can call
  any tool. In production, every MCP server needs an auth layer (API key, OAuth
  token, or mTLS). Without this, a rogue agent can drain inventory data or
  trigger payments.

- [Identity] No caller identity on tool calls. When the inventory server
  receives a get_product call, it cannot verify which agent called it. Audit
  trails are incomplete: you know a tool was called but not who called it.
  Phase 8 wires DNSid (Domain Name System identity) so tool calls can carry caller identity.

- [Scoping] Tool schema trust. The agent trusts the tool's schema description
  to understand what the tool does. A malicious MCP server could advertise a
  benign schema while doing something harmful. There is no signed schema registry
  in the current MCP spec.

**Why this matters:**
MCP is the nervous system of the stack. Every agent capability flows through it.
The protocol is excellent at standardization; the security posture is left
entirely to the implementor. Getting MCP auth right is a prerequisite for
production deployment of any phase above it.

---

## Phase 2: UCP — Universal Commerce Protocol

**Type:** Protocol
**Established by:** Google, co-developed with Shopify, Walmart, Target, Etsy,
Wayfair, PayPal, and Stripe. Announced NRF January 11 2026. Version
google-ucp:v2026-04-08 released April 8 2026 under Apache 2.0.
**Adoption:** Early but high-signal coalition covering a significant share of
US e-commerce GMV.
**Maturity:** Maturing. Real spec with major retailer adoption, but merchant-level
implementation still rolling out as of mid-2026.

**Problem it solves:**
Product catalogs are a Tower of Babel: every seller uses different field names,
formats, and schemas. UCP defines a machine-readable catalog format using
JSON-LD and schema.org so any buyer agent can parse any seller's catalog
without custom code per seller.

**How we used it:**
JSON-LD product catalog at `/.well-known/ucp.json`. The Buyer Agent fetches
this and selects products using rule-based logic — no LLM needed — because the
schema is predictable. seller_agent/ucp_profile.py generates the UCP profile
and checkout session endpoints.

**Dependencies and sequencing:**
Requires MCP (Model Context Protocol) (Phase 1) for the inventory data that populates the catalog.
Without UCP, the buyer agent has no machine-readable way to discover what the
seller offers — it would require custom parsing per seller. Phase 12 (ACP)
extends this by adding a second catalog protocol; without UCP in place first,
Phase 12 has nothing to route from.

**Alternatives considered:**
- ACP (Agentic Commerce Protocol) (OpenAI + Stripe, Phase 12) is the main competitor at this layer.
  UCP is backed by Google, Walmart, Shopify, Target, Etsy, Wayfair, PayPal, and Stripe, and targets
  any buyer agent across any platform. ACP is backed by OpenAI and Stripe and is optimized for
  the ChatGPT shopping agent ecosystem. UCP (Universal Commerce Protocol) was the learning target for this phase; ACP (Agentic Commerce Protocol) was added as a second learning target in Phase 12.
- Proprietary catalog formats (CSV exports, custom JSON) remain common in
  practice but require custom integration per seller — exactly the problem UCP
  solves.
- Schema.org alone (without UCP's checkout journey extension) handles catalog
  discovery but not cart, checkout, or order status. UCP extends schema.org
  to cover the full commerce lifecycle.

**Security loopholes:**

- [Identity] Catalog poisoning. UCP catalogs are public JSON documents.
  Nothing in the UCP spec prevents a man-in-the-middle from serving a modified
  catalog with inflated prices or fraudulent SKUs. Mitigation: sign the catalog
  document with the seller's secp256k1 key (Phase 7) and have the buyer verify
  the signature before trusting catalog data.

- [Scoping] Schema conformance without enforcement. A seller can claim
  google-ucp:v2026-04-08 compliance while serving non-compliant fields.
  The buyer agent has no way to know without running a schema validator.
  SupplyMind does not currently validate incoming UCP documents before parsing.

- [Approvals] No freshness guarantee. The buyer agent caches the catalog
  between requests. A seller could change prices between the buyer's catalog
  fetch and the purchase order. Solved at the cart level in UCP's checkout
  journey extension and in AP2 (Agentic Payment Protocol) Cart Mandates (Phase 9).

**Why this matters:**
UCP solves the Tower of Babel problem for catalog data. But a shared schema
only creates interoperability — it does not create trust. Catalog tells you
what a seller offers; it does not prove the catalog is authentic or current.
UCP + secp256k1 signatures + AP2 Cart Mandates is the complete picture.

---

## Phase 3: Agent Discovery + Micro-payment (A2A + x402)

### Phase 3a: A2A — Agent-to-Agent Protocol

**Type:** Protocol
**Established by:** Google DeepMind (April 2025, 50 founding partners).
Contributed to Linux Foundation Agentic AI Foundation June 2025. Now at
version 1.2, with signed Agent Cards and cryptographic domain verification.
**Adoption:** 150+ organizations in production as of April 2026, including
Microsoft, AWS, Salesforce, SAP, ServiceNow, and IBM.
**Maturity:** Maturing. LF-governed, v1.2 with signed cards, strong enterprise
adoption, but discovery at open-web scale still relies on external registries.

**Problem it solves:**
When two AI agents need to collaborate, how do they find each other and
coordinate work? A2A defines a discovery mechanism (Agent Cards at
/.well-known/agent-card.json) and a task lifecycle (submit, poll, complete)
so agents can transact without human coordination at each step.

**How we used it:**
Seller publishes an Agent Card listing capabilities and task endpoint. Buyer
fetches this card, sends purchase orders to POST /tasks/send, and polls
GET /tasks/{id} for confirmation.

**Dependencies and sequencing:**
Requires UCP (Universal Commerce Protocol) (Phase 2) for the seller to have something meaningful to advertise
in its Agent Card capabilities. Without A2A, buyer and seller have no standard
discovery or task coordination mechanism — every interaction requires knowing
the seller's URL in advance. Phase 6 — NANDA (Networked Agents and Decentralized Architecture) — extends A2A discovery to the open
web; without A2A Agent Cards, NANDA has no standard format to index.

**Alternatives considered:**
- OpenAI Agents SDK coordination patterns handle multi-agent orchestration
  within the OpenAI ecosystem but are not interoperable with non-OpenAI agents.
- LangGraph provides agent coordination for LangChain-based systems but is a
  framework, not a protocol — no standard wire format for cross-vendor agents.
- Direct REST without discovery is viable for known, fixed seller URLs but
  does not scale to an open marketplace where sellers are unknown in advance.
- A2A (Agent-to-Agent) was the learning target for this phase. A2A is the only published, LF-governed agent coordination protocol with real enterprise adoption at the time of implementation.

**Security loopholes:**

- [Identity] Agent Card spoofing. The Agent Card is a JSON document at a
  well-known URL. Any server can serve a card claiming to be any agent. A DNS
  hijack or BGP route leak could redirect the buyer to a fraudulent seller.
  A2A v1.2 adds signed Agent Cards with cryptographic domain verification.
  Phase 8 adds DNSid (Domain Name System identity) ownership verification on top.

- [Identity] Task endpoint trust. The buyer sends purchase orders to whatever
  URL the Agent Card specifies. If the card is spoofed, orders go to the
  attacker. There is no challenge-response to confirm the task endpoint is
  controlled by the same entity that signed the card.

- [Scoping] No task integrity. Once a task is submitted, the task contents
  are trusted as-is. There is no mechanism in A2A to verify that the task was
  not modified in transit. AP2 (Agentic Payment Protocol) Cart Mandates (Phase 9) solve this by signing
  cart contents before submission.

- [Enforcement] Polling is trust without verification. When the buyer polls
  GET /tasks/{id}, the response could be fabricated. The buyer has no way to
  verify the task result was produced by the same agent that received the order.
  A signed task result using the seller's secp256k1 key would close this gap.

**Why this matters:**
A2A standardizes discovery and task coordination but assumes a trusted network.
In the open agentic web, the network is not trusted. Every A2A interaction
needs the identity layers from Phases 7 and 8 underneath it to be
production-safe. Discovery without verified identity is a phone book — it tells
you where someone claims to be, not who they actually are.

---

### Phase 3b: x402 — HTTP 402 Payment Required

**Type:** Protocol
**Established by:** Coinbase (open-sourced May 2025). x402 Foundation launched
April 2 2026, co-founded by Coinbase and Linux Foundation. Coalition includes
Stripe, Cloudflare, AWS, Google, Microsoft, Visa, and Mastercard.
**Adoption:** 119 million transactions on Base, 35 million on Solana as of
March 2026. ~$600M annualized protocol volume, ~$28,000 daily real commerce volume.
**Maturity:** Maturing. LF foundation, major coalition, real transaction volume,
but on-chain verification infrastructure still maturing in tooling.

**Problem it solves:**
Bulk pricing data is valuable. Without a gate, any agent -- legitimate or
scraping -- can request it for free at any volume. x402 solves this with an
access control mechanism: the server returns an HTTP 402 response with a
micro-payment challenge, the client pays a small USDC amount, retries with
proof of payment, and receives the protected data. The micro-payment is not
the purchase price -- it is the cost of accessing the pricing tier. The
actual purchase is handled separately by AP2 (Agentic Payment Protocol).
x402 repurposes HTTP's dormant 402 status code for this pay-per-request
pattern, making it native to the web without any additional protocol layer.

**How we used it:**
Bulk quotes above $500 trigger a 402 response with USDC payment instructions.
The buyer agent reads the challenge, simulates a USDC micro-payment, and retries
with a transaction hash in the X-Payment header. The seller gate accepts any
non-empty header in the current prototype. Real on-chain verification of the
payment hash is outside the current scope of SupplyMind.

**Dependencies and sequencing:**
Requires A2A (Agent-to-Agent) (Phase 3) for the buyer to have found the seller
and initiated a task before a payment challenge arises -- x402 fires inside
an ongoing A2A task, not as a standalone interaction. Phase 8 (DNSid
(Domain Name System identity)) adds an identity gate that must pass before
x402 fires, so only verified agents reach the pricing tier. Phase 13 (Agent
Wallet Layer) provides the funded wallet required for real on-chain settlement.
Skipping x402 means bulk quotes have no access control -- any agent can
request them for free.

**Alternatives considered:**
- Stripe metered billing handles per-request API charging but requires a
  Stripe account, monthly invoices, and a human billing relationship — too
  heavy for machine-to-machine micropayments between unknown agents.
- Traditional API keys with rate limiting prevent abuse but do not create
  economic signals — a key either works or it does not, with no per-use cost.
- Lightning Network micropayments achieve similar per-request economics using
  Bitcoin but require Lightning node infrastructure on both sides; x402 on
  Base is simpler to deploy and uses stablecoins (no price volatility).
- x402 was the learning target for this phase. x402 is the LF-governed protocol with the strongest payment network coalition and native USDC support on Base at the time of implementation.

**Security loopholes:**

- [Enforcement] Payment proof is not verified. The seller currently accepts
  any non-empty X-Payment header. A malicious buyer can send a fake transaction
  hash and receive the quote without paying. This is the most critical open gap.
  Mitigation: query the blockchain to confirm the transaction hash, amount, and
  target wallet before releasing the quote.

- [Enforcement] Replay attacks. A valid X-Payment header from a previous
  transaction can be replayed to get the same resource again without paying.
  x402 requires nonce or timestamp validation to prevent this. SupplyMind
  does not currently implement replay prevention.

- [Identity] Payment challenge integrity. The 402 response contains a payment
  address and amount. If an attacker intercepts the 402 response and substitutes
  their own wallet address, the buyer pays the attacker instead of the seller.
  HTTPS is the first mitigation; signing the payment challenge with the seller's
  secp256k1 key is the second.

- [Identity] DNSid (Domain Name System identity) gate missing. The x402 flow currently does not verify the
  counterparty's identity before accepting payment. Phase 8 adds this gate:
  resolve the counterparty's DNSid before the micro-payment fires, and reject
  if revoked.

**Why this matters:**
x402 is the first protocol in this stack that moves real value. Every security
gap in x402 has a direct financial consequence. The current implementation is
appropriate for local development but is not production-safe without on-chain
verification, replay prevention, and DNSid gating.

---

## Phase 4: Procurement Loop (AP2 + ACF + MPP)

### Phase 4a: AP2 — Agent Payments Protocol

**Type:** Protocol
**Established by:** Google (September 16 2025). 60+ founding partners including
PayPal, Mastercard, American Express, Adyen, Coinbase, Salesforce, and Worldpay.
Apache 2.0. AP2 v0.2.0 released May 2026 adding Human Not Present payments and
cryptographic Mandates.
**Adoption:** Broad institutional backing from day one. Maturing enterprise
integration as of mid-2026.
**Maturity:** Maturing (v0.1 as implemented). Experimental (v0.2.0 signed
mandates — announced May 2026, implementations nascent).

**Problem it solves:**
An AI agent with unrestricted payment authority is a liability. AP2 defines
spending Mandates: structured contracts the human sets once and the agent
enforces on every payment. The agent can only pay approved sellers, up to
defined limits, under defined conditions.

**How we used it (Phase 4, v0.1):**
Mandate created before every procurement run: approved sellers, per-transaction
limit, total spend limit. Every payment calls check_mandate() first, enforced
in the payment server, not in the agent's logic.

**Phase 9 upgrade (AP2 v0.2.0):**
Adds signed Intent Mandates (human signs upfront) and Cart Mandates (agent
signs at purchase time linking back to Intent Mandate). Creates a
non-repudiable cryptographic audit trail from human intent to payment execution.

**Dependencies and sequencing:**
Requires x402 (Phase 3) to already be in place as the micro-payment rail that
AP2 governs. Phase 7 (secp256k1) is required for Phase 9's signed mandates —
without a keypair, you cannot sign Intent or Cart Mandates. Phase 8 — DNSid (Domain Name System identity) —
is required to replace string-based seller approval with ownership-verified
counterparty checks. Skipping AP2 means the agent has no spending policy —
the financial risk is unbounded.

**Alternatives considered:**
- Mastercard Verifiable Intent (Phase 14) addresses the same audit trail
  problem from the card network side rather than the protocol side. They are
  complementary: AP2 governs the agent's spending policy; Verifiable Intent
  creates a tamper-resistant network-level record of human consent. SupplyMind
  implements both in their respective phases.
- OpenAI's consent model for agent payments is tightly coupled to the OpenAI
  ecosystem and not interoperable with Claude-based buyers.
- No mandate (trust the agent) is viable for low-risk internal automation but
  not for procurement involving external sellers and real funds.
- AP2 (Agentic Payment Protocol) was the learning target for this phase. AP2 has Google's institutional backing, a 60+ partner coalition, and explicit B2B procurement use case alignment.

**Security loopholes:**

- [Approvals] Mandate is unsigned. The current mandate is a Python dict in
  memory. There is no cryptographic proof it was set by the authorized human
  and not modified by the agent process. Phase 9 signs mandates with the
  human's secp256k1 key, making tampering detectable. In production, this
  signing step would be performed by LoginID FIDO2: the private key lives
  in hardware, and a biometric gesture by the human is required to produce
  the signature.

- [Enforcement] In-memory mandate store. MANDATES is a module-level dict that
  does not survive process restart. If the payment server crashes, all mandates
  are lost and the agent has no spending policy until a new one is created.
  Mitigation: persist mandates to SQLite with signatures.

- [Identity] Approved seller list is a string match. The approved_sellers field
  is checked by string equality. Nothing prevents a malicious agent from
  registering with an ID that matches an approved seller. Phase 8 replaces
  string matching with DNSid resolution and ownership verification.

- [Enforcement] No mandate-to-transaction linkage. After a payment is approved,
  there is no cryptographic link between the mandate decision and the payment
  execution. An audit trail showing a payment happened but not that it was
  mandate-approved is incomplete for compliance.

**Why this matters:**
AP2 is the governance layer of the stack. The v0.1 implementation is a correct
proof of concept but would not pass a compliance review at a financial institution.
The v0.2.0 upgrade in Phase 9 closes the most critical gaps by making the entire
chain from human intent to payment execution cryptographically verifiable.

---

### Phase 4b: ACF — Agentic Commerce Framework

**Type:** Framework
**Established by:** Vincent Dorange, 2025. Governed at acfstandard.com.
Independent. Four principles: Decision Sovereignty, Governance by Design,
Ultimate Human Control, and Traceable Accountability.
**Adoption:** Niche but influential in governance discussions, particularly
in European regulatory contexts.
**Maturity:** Experimental. No formal spec, no LF governance, limited
production implementations.

**Problem it solves:**
Binary human approval does not scale with agentic commerce. ACF defines tiered
autonomy: small payments execute automatically, medium payments execute with a
notification, large payments require explicit human approval.

**How we used it:**
Three tiers: AUTO (under $5), NOTIFY ($5-$10), BLOCK (over $10). Thresholds
are set by the human operator and encode risk tolerance, not agent intelligence.

**Dependencies and sequencing:**
ACF tiers are implemented inside the AP2 (Agentic Payment Protocol) mandate check. Without AP2 (Phase 4),
ACF has no enforcement mechanism — it is just a naming convention. Phase 9
makes the tier thresholds part of the signed Intent Mandate, which means
changing them requires re-signing.

**Alternatives considered:**
- Binary approve/deny is the simplest model: every payment requires human
  approval, or none do. It does not scale but has zero governance complexity.
- Human-in-the-loop for all payments is the conservative enterprise default
  but eliminates the autonomy that makes agentic procurement valuable.
- Dynamic risk scoring (adjusting tiers based on vendor history, time of day,
  or anomaly signals) is more sophisticated than fixed tiers but requires
  infrastructure SupplyMind does not currently have. Dynamic risk scoring is
  outside the current scope of SupplyMind.
- ACF (Agentic Commerce Framework) was the learning target for this phase. ACF's tiered autonomy model is the simplest approach that preserves human oversight without requiring human action on every transaction.

**Security loopholes:**

- [Scoping] Thresholds are configuration, not policy. The ACF tier values are
  constants in code. Any code change or environment variable override can
  silently widen the AUTO band. Mitigation: include tier thresholds in the
  signed AP2 Intent Mandate (Phase 9) so changes invalidate the signature.

- [Approvals] NOTIFY is fire-and-forget. The NOTIFY tier logs a notification
  but does not wait for human acknowledgment. In high-throughput scenarios,
  thousands of NOTIFY payments could execute before a human reviews the log.

- [Enforcement] BLOCK requires terminal interaction. In a headless production
  deployment, there is no terminal. BLOCK would fail silently or hang.
  Mitigation: replace terminal prompts with a webhook or message queue monitored
  via the governance dashboard (Phase 11).

**Why this matters:**
ACF's tiered autonomy is the design pattern that makes human oversight scalable.
The security risk is that policy is only as durable as the code that enforces it.
Phase 9 makes the policy cryptographically durable.

---

### Phase 4c: MPP — Machine Payments Protocol

**Type:** Protocol
**Established by:** Stripe and Tempo (March 18 2026). Extended at Stripe
Sessions 2026 (April 29-30). Rail-agnostic: wraps stablecoins, cards, and
Lightning under a single lifecycle-aware envelope.
**Adoption:** Early, high-credibility. Visa, Lightspark, Affirm, and Klarna
have published extensions.
**Maturity:** Experimental. Launched March 2026, early real-world deployment,
spec still evolving.

**Problem it solves:**
Different sellers accept different payment rails. MPP provides a payment
abstraction layer where the agent declares intent and the rails figure out
execution.

**How we used it:**
Dual rails simultaneously: fiat rail (Stripe PaymentIntent in test mode) and
USDC rail (simulated Circle USDC transfer). Both return a uniform result
envelope. The ACF (Agentic Commerce Framework) governance layer sits above both rails.

**Dependencies and sequencing:**
Requires AP2 (Agentic Payment Protocol) (Phase 4) to have already authorized the payment before MPP
executes it. MPP handles execution; AP2 handles authorization. Skipping MPP
means the agent must know which rail to use for each transaction — it becomes
the agent's problem rather than the payment abstraction layer's problem.

**Alternatives considered:**
- Stripe alone (fiat only) is simpler but excludes the stablecoin settlement
  path needed for x402 micro-payments.
- Circle Programmable Wallets alone (stablecoin only) excludes merchants who
  only accept card payments.
- AWS AgentCore Payments is a managed implementation of x402 and Coinbase/Stripe
  rails -- essentially MPP (Machine Payments Protocol) as a service. SupplyMind
  builds MPP manually to understand the plumbing; AgentCore is the managed
  alternative for a production deployment.
- Stripe Treasury abstracts ACH, wire, and card rails behind one API but does
  not cover stablecoin/x402, which is the gap that matters for agentic commerce.
  Strong for fiat-only enterprise procurement.
- Moov is open-source financial infrastructure that abstracts ACH, RTP
  (Real-Time Payments), card, and wire. No stablecoin support. More
  developer-controlled than Stripe Treasury; good for regulated fiat workflows.
- Bridge (acquired by Stripe) is a stablecoin-to-fiat abstraction layer that
  converts USDC to fiat at settlement, making the rail choice transparent to
  the merchant. The closest production option to a true multi-rail abstraction
  covering both card and stablecoin.
- MPP (Machine Payments Protocol) was the learning target for this phase. MPP
  proposes to cover all three rails (card, ACH/wire, stablecoin) behind a single
  API. Nothing in production today does this fully. MPP is experimental precisely
  because that three-rail abstraction does not yet exist as a production product.
  AWS AgentCore is the nearest practical approximation for the x402 + Stripe
  combination SupplyMind implements.

**Security loopholes:**

- [Scoping] Rail selection is unverified. The implementation runs both rails
  and returns whichever succeeds first. No policy governs which rail should
  be used for which transaction type. Phase 13 introduces explicit payment
  routing policy by transaction size.

- [Enforcement] USDC transfer is simulated. There is no on-chain settlement.
  This is appropriate for development but must be replaced before real value flows.

- [Enforcement] No settlement finality check. The implementation returns
  success as soon as the Stripe PaymentIntent is created, not confirmed.
  Payment creation and payment settlement are different states.

**Why this matters:**
MPP is the abstraction that prevents the agent from needing to understand rails.
The security implication is that an abstraction layer can hide failures. The
governance dashboard (Phase 11) makes rail behavior visible so operators can
detect silent failures.

---

## Phase 5: Protocol Reflection + Second Seller

**Type:** Analysis + Implementation
**Status:** Done.

**Problem it solves:**
After Phase 4, the system works end-to-end but with a single seller and no
competitive dynamics. Phase 5 adds a second seller agent (QuickSupply Co.
on port 8081) with independent pricing, tests competitive price discovery
across both catalogs, and documents the full protocol reflection for Phases 1-4.

**What was completed:**
Full protocol reflection across Phases 1-4 (this document). Second seller
implementation: QuickSupply Co. runs as a second instance of the seller agent
with a 12% price discount applied via --price-multiplier. Four new functions
in src/buyer_agent/buyer.py implement the multi-seller flow:

- discover_sellers(): fetches A2A (Agent-to-Agent) agent cards from a list of seller URLs
- fetch_all_catalogs(): fetches UCP (Universal Commerce Protocol) catalogs from all discovered sellers
- select_best_products_multi(): cheapest-wins selection per shopping list item across all catalogs
- run_multi_seller_flow(): orchestrates discovery, comparison, order splitting, and submission

QuickSupply Co. is registered in the DNSid (Domain Name System identity) registry under
dnsid://quicksupply.localhost/agents/seller-001. Both sellers have active
handles verifiable at runtime.

**Buyer decision logic:**
Rule-based, cheapest-wins per item. For each item on the shopping list, all
seller catalogs are scanned and the matching product with the lowest unit price
is selected. A single procurement run may be split across multiple sellers:
one seller wins on paper, another on pens, based solely on price. No vendor
loyalty, no bundle discount logic, no minimum-order enforcement in the prototype.

**Mandate location:**
The human issues one AP2 (Agentic Payment Protocol) Intent Mandate before the
multi-seller flow starts. The approved_sellers field in that mandate contains
both seller DIDs: did:web:localhost:8080 (SupplyMind Seller) and
did:web:localhost:8081 (QuickSupply Co.). When the buyer submits a Cart Mandate
to a seller, verify_cart_mandate() checks that the seller's DID appears in the
Intent Mandate's approved_sellers list. Both sellers are pre-approved in a
single mandate; no separate mandate is issued per seller. A third seller discovered via NANDA (Phase 7) that is not in approved_sellers
is rejected without human re-authorization.

**Dependencies and sequencing:**
The competitive discovery pattern directly enables Phase 7 NANDA (Networked
Agents and Decentralized Architecture): the same discover_sellers() and
select_best_products_multi() logic works whether seller URLs come from a
hardcoded list or from a NANDA registry search. Phase 7 replaces the input
source; the comparison and routing logic is unchanged.

**Why this matters:**
Multi-seller competition is the mechanism that makes agentic procurement
economically meaningful for buyers. A buyer agent that can only buy from one
known seller is a workflow tool. A buyer agent that discovers, compares, and
selects from multiple verified sellers is an economic actor.

---

## Phase 6: KYA + Cryptographic Identity (secp256k1, DID, KYA)

**Type:** Framework (with W3C DID spec as the underlying protocol)
**Established by:** DID (Decentralized Identifier) spec by W3C. KYA (Know Your Agent) as a pattern by MIT and industry
(Sumsub, Trulioo) circa 2025. secp256k1 is the same elliptic curve used by
Bitcoin and Ethereum.
**Adoption:** Emerging. DID:web is widely understood; production KYA
implementations are nascent.
**Maturity:** Maturing (secp256k1 + DID — battle-tested cryptography).
Experimental (KYA as an agent identity pattern — nascent implementations).

**Problem it solves:**
KYA (Know Your Agent) is symmetric: both sides of a transaction need it.

The buyer needs to verify the seller is legitimate before sending money. The
seller equally needs to verify the buyer is who it claims to be before
fulfilling an order -- an unverified buyer agent could be placing orders it
has no authority or funds to honor.

KYA uses cryptographic proof: each party publishes a signed identity document.
The counterparty verifies the signature using the published public key. No
centralized authority is needed.

DID (Decentralized Identifier) answers "who are you?" KYA answers "what are
you, who operates you, and what are you authorized to do?" A DID gives an
agent a verifiable name tied to a domain. KYA uses that same key to publish
a richer signed credential: operator identity, capabilities, spending limits,
and authorization chain.

In production, every human-initiated signing step on both sides -- operator
authorizing the seller agent, human authorizing the buyer agent -- is performed
with LoginID FIDO2 biometric. The secp256k1 file-based key in SupplyMind
simulates that ceremony. LoginID replaces the file with a hardware-attested
biometric that cannot be copied or exfiltrated.

**Buyer-side KYA: the market**
Buyer-side KYA is where significant investment is concentrating as of mid-2026.
Two distinct approaches are emerging:

Skyfire ($9.5M raised, a16z CSX + Coinbase Ventures) takes a credential-issuer
approach: it issues KYAPay (Know Your Agent Pay) tokens -- signed JWTs (JSON
Web Tokens) that assert who built the buyer agent, who authorized it, and what
it is allowed to spend. Skyfire's partnership with Experian (confirmed April
2026) enriches KYA tokens with Experian's identity and fraud signal data,
issuing a risk score tied to the human principal. Experian's own materials
describe continuous behavioral scoring that can shift before a transaction
completes -- this is not a static score attached once at issuance. KYAPay token
expiry per the IETF draft spec is 10 seconds to 24 hours (not 90 days as
previously stated). Whether KYAPay has a defined revocation mechanism is
unconfirmed from available spec documentation.

Baselayer ($6.5M seed, Torch Capital + Founder Collective + Afore) takes a
business-graph approach: it evaluates the legal entity behind the buyer agent
against authoritative records including SOS filings, EIN, and OFAC screening,
and issues a business risk assessment. Real-time evaluation capability is a
stated product feature. Whether this includes phone and email enrichment, how
it compares to Experian's approach in depth or speed, and whether it is
genuinely ahead of Skyfire on buyer-side KYA are not confirmed -- these require
direct product evaluation.

These two approaches address different questions: Skyfire answers "is this agent
properly delegated by a verified human?", Baselayer answers "is the business
behind this agent real and clean?" A complete buyer-side identity stack likely
needs both. Which is more complete today is not established.

**The Firmly + LoginID buyer-side opportunity**
Firmly's current positioning is merchant-facing (seller side). LoginID's
current positioning is human authentication. The buyer-side KYA gap is an
expansion path for both, but it is not a natural extension -- it requires
moving toward the buyer's organization, which is a different sales motion,
different compliance requirements, and direct competition with Skyfire and
Baselayer on their home ground.

The structural question is whether Firmly wants to own both sides of the
transaction trust stack or focus on making the seller side defensible first.
Owning both sides is the stronger moat: a buyer agent credentialed by Firmly
and a seller agent credentialed by Firmly create a closed trust loop that
neither Skyfire nor Baselayer can replicate from their current positions.
But it is a significantly larger product and go-to-market bet.

**How we used it:**
secp256k1 keypair generated and persisted in .keys/seller_private_key.hex
(gitignored). DID derived as did:web:localhost:8080. KYA document built and
signed in src/identity/kya_builder.py. NANDA AgentFacts signed with the same
key in src/seller_agent/nanda_facts.py. Buyer can verify any signed document
using verify_signature() from src/identity/keys.py. Buyer-side KYA was not
implemented in SupplyMind -- the buyer agent identifies itself via BUYER_ID
(a DID string) but does not publish a signed KYA document. That is the gap
this phase leaves open on the buyer side.

**Dependencies and sequencing:**
Phase 6 is the cryptographic foundation for Phases 7, 8, 9, and 14. DNSid (Domain Name System identity)
(Phase 7) anchors the key to a DNS domain. Signed Mandates (Phase 8) use the
same signing infrastructure. Visa TAP (Trusted Agent Protocol) (Phase 14) adds a network-level credential
on top of the key-based identity. NANDA (Phase 7) uses the same key to sign
the AgentFacts registration document. Skipping Phase 6 means every downstream
phase that requires signatures has nothing to sign with.

**Alternatives considered:**
- ENS (Ethereum Name Service) provides human-readable names anchored on
  Ethereum mainnet. More decentralized than did:web but requires on-chain
  transactions to register and update, adding cost and latency.
- did:ion (Microsoft, Bitcoin-anchored) provides stronger decentralization
  guarantees than did:web but requires Bitcoin infrastructure and is slower
  to resolve.
- did:key requires no infrastructure at all (the key is the identifier) but
  provides no revocation mechanism — once a key is compromised, there is no
  way to signal that to counterparties. This makes it unsuitable for production.
- did:web was the learning target for this phase. did:web requires no blockchain infrastructure, is fast to resolve, and is the most widely supported DID (Decentralized Identifier) method. The
  revocation gap is addressed by DNSid in Phase 7.

**Security loopholes:**

- [Identity] No key revocation. If the private key is compromised, there is
  no way to signal that signatures from that key should no longer be trusted.
  Every signed document from the compromised key remains cryptographically valid
  until all relying parties rotate their trust anchor. DNSid (Phase 7) solves
  this: the DNSid registry can mark an agent as revoked regardless of signature
  validity.

- [Identity] Key-to-owner binding is asserted, not proven. The KYA document
  says the key belongs to "SupplyMind Operator." Nothing prevents anyone from
  generating a key and claiming the same owner name. DNSid anchors the key to
  a DNS domain, which requires real-world control of a registered domain to spoof.

- [Identity] Private key file security. The key is stored in a plaintext hex
  file on disk. Production mitigation: HSM, cloud KMS, or hardware wallet.
  Gitignoring the .keys/ directory is necessary but not sufficient.

- [Identity] DID:web depends on domain control. A did:web identifier resolves
  by fetching a JSON document from a URL. A DNS hijack can serve a different
  DID document with a different public key. DNSSEC mitigates this.

- [Scoping] Signature covers content, not context. The signature proves the
  document was signed by the key at some point. It does not prove the document
  reflects current state. A signed KYA from six months ago is still
  cryptographically valid. Mitigation: include expiry timestamps and require
  re-signing at regular intervals.

- [Identity] Seller-side ownership chain stops at the company, not the human.
  DNSid proves a company controls a domain. The KYA document names an operator.
  Neither is verified against a human identity registry. A fraudulent seller
  can control a real DNS record and produce a clean KYA document. The buyer
  side goes one level higher via Skyfire/KYAPay: Experian verifies the human
  principal behind the buyer agent. No equivalent exists on the seller side.
  Baselayer's SOS/EIN/OFAC checks on the business entity partially close this
  gap, but seller-side human identity verification has no confirmed solution
  in the current market.

**Why this matters:**
Cryptographic identity is necessary but not sufficient for enterprise trust.
It answers "was this signed by the claimed key?" but not "should I trust this
key?" The answer to the second question requires ownership registries (DNSid),
network-level credentials (Visa TAP, Mastercard Agent Pay), and revocation
infrastructure. Phase 6 lays the foundation; Phases 7 and 14 make it
enterprise-grade.

**The missing layer: business entity verification (KYA gap)**

Phase 6 proves the agent signed its own credential. DNSid (Phase 7) proves
the agent controls a domain. Neither answers the question that every payment
rail, lender, and supplier actually needs: is the business behind this agent
real, solvent, and legally clean?

This is the KYA gap. An agent can have a perfect secp256k1 signature and a
valid DNSid handle and still represent a shell LLC incorporated yesterday at
a vacant lot, sanctioned, or under active litigation. Cryptographic identity
and business entity verification are orthogonal problems. The first proves
the agent is who it claims to be. The second proves the claimed entity is
worth trusting.

Who fills this gap and what Firmly + LoginID can and cannot do:

| Layer | Who solves it | What it proves |
|---|---|---|
| Agent key is legitimate | secp256k1 / LoginID (Phase 6) | Request was signed by the claimed key |
| Agent's domain is controlled | DNSid (Phase 8) | Operator controls the DNS record, can revoke |
| Human behind the agent is real | Experian via Skyfire KYAPay | Human identity, credit history, fraud signals |
| Business entity is real and clean | Baselayer | SOS filing, EIN, OFAC status (confirmed scope) |

Firmly + LoginID own the top two rows. The FIDO2 biometric (LoginID) replaces
the secp256k1 file key with a hardware-backed human gesture. DNSid binds the
credential to domain ownership and enables real-time revocation. Together they
answer: "the agent is who it claims, and the human behind it explicitly
authorized this."

The bottom two rows are outside Firmly and LoginID's current scope. No amount
of cryptographic work at Phase 6 substitutes for SOS/EIN/OFAC checks. The
question "is the business entity behind this agent real and solvent?" requires
a data partnership with authoritative business registries -- which is exactly
what Baselayer is built to answer and what Experian provides at the human level
via Skyfire. These are complementary services, not competitors: Firmly + LoginID
win by proving the agent and the human; Skyfire and Baselayer win by proving
the entities. A complete trust stack requires all four layers.

---

## Phase 7: NANDA — Decentralized Agent Registry

**Type:** Protocol (W3C Verifiable Credential + REST registry)
**Established by:** Project NANDA (projectnanda.org). Open, decentralized.
No single governing organization.
**Adoption:** Early. NANDA NEST is the production registry. Registration
requires HTTPS endpoints; localhost deployments are structurally excluded.
**Maturity:** Experimental. Live registry, but governance model and spec
stability are still forming.

**Problem it solves:**
How does a buyer agent find a seller agent it has never interacted with,
without knowing its URL in advance? NANDA (Networked Agents and Decentralized
Architecture) is a decentralized registry where agents publish their
capabilities as W3C Verifiable Credentials. Any agent can search NANDA and
find peers by capability, tag, or DID (Decentralized Identifier).

**How we used it:**
AgentFacts document (W3C VC, JSON-LD) generated by src/seller_agent/nanda_facts.py.
Signed with the seller's secp256k1 key from Phase 6. Attempted registration to
nest.projectnanda.org (rejected for localhost, expected behavior). Structure
is production-ready; deployment requires a public HTTPS host.

**Dependencies and sequencing:**
Requires Phase 6 (secp256k1 + KYA) to have run first. The NANDA AgentFacts
document is signed with the same key as the KYA document. Without that signed
identity, NANDA registration is self-asserted with no proof. Phase 8 — DNSid (Domain Name System identity) —
adds an ownership verification gate that should run after NANDA discovery
and before any transaction begins.

**Alternatives considered:**
- Enterprise service registries (Consul, etcd, API gateways) handle agent
  discovery within a single organization but are not interoperable across
  organizational boundaries — exactly the open marketplace problem SupplyMind
  is trying to solve.
- Centralized directories (a single org maintaining a curated agent list) are
  simpler to operate but create a strategic dependency: the directory owner
  decides who is listed, what the trust signal means, and can deprioritize
  or exclude participants at will. A platform like Firmly would be building
  on ground it does not control.
- NANDA was the learning target for this phase. NANDA is the only open,
  decentralized, W3C-VC-based agent registry available. The HTTPS constraint
  is a known limitation for local development.

**Security loopholes:**

- [Identity] Registration is self-asserted. Any agent can register on NANDA
  claiming any capability. NANDA does not verify that the agent implements
  what it advertises. Phase 8 adds DNSid ownership verification as the
  post-discovery trust gate.

- [Identity] DID ownership is unverified at discovery time. The NANDA
  registration includes a DID but NANDA does not verify the registrant controls
  the corresponding private key. Two agents could register with the same DID.
  The buyer must verify the seller's KYA signature before trusting any
  registration data.

- [Scoping] HTTPS requirement creates centralization pressure. NANDA requires
  HTTPS, which requires a domain and certificate, effectively excluding
  private or enterprise-internal agents from the open registry. This is a
  protocol design tradeoff, not a bug.

**Why this matters:**
NANDA solves agent discoverability at open web scale. The security model is
defense-in-depth: NANDA finds candidates, KYA (Phase 6) verifies identity,
DNSid (Phase 8) verifies ownership, A2A (Agent-to-Agent) coordinates the task.
No single layer is sufficient alone.

**Production note: OpenClaw as buyer agent runtime**
OpenClaw (openclaw.org, MIT-licensed, OpenClaw Foundation) is a widely adopted
open-source agent runtime (15k+ GitHub stars as of early 2026). A production buyer agent
could run on OpenClaw instead of the custom buyer.py built in SupplyMind.
OpenClaw supports NANDA NEST registration natively (via ClawNanda), runs on
Maritime or any self-hosted environment, and works with Claude, GPT-4o, and
Gemini. The A2A, UCP, AP2, and mandate chain protocols SupplyMind implements
are runtime-agnostic: an OpenClaw buyer would call the same endpoints and
follow the same flow as buyer.py. OpenClaw adds deployment convenience and
multi-channel access (Telegram, Slack, WhatsApp) but introduces no new
protocol. It is a deployment choice, not a protocol phase.

The traditional KYB (Know Your Business) process was designed for humans
filling out forms reviewed by other humans. It cannot run at agent speed.
When a buyer agent and seller agent negotiate a procurement contract in
seconds, there is no time for a compliance analyst to pull a D&B report,
check references, and screen OFAC. A machine-readable, real-time trust
oracle has to exist at the protocol layer.

Without it, every agentic payment rail, every trade credit workflow, and
every merchant onboarding process either falls back to human intervention
(which defeats the purpose of agents) or accepts unverified counterparties
(which opens the door to fraud at machine speed).

**Market landscape: who is building this layer (as of June 2026)**

This gap has attracted real capital and enterprise attention. The emerging
category is sometimes called the "agent trust layer" or "KYA infrastructure."

| Player | Approach | Signal |
|--------|----------|--------|
| Baselayer | Business identity verification against SOS filings, EIN, OFAC. Real-time risk assessment. B2B focus. | $6.5M seed (Torch Capital, Founder Collective, Afore). |
| Skyfire | KYAPay (Know Your Agent Pay) protocol: signed JWTs (JSON Web Tokens) carrying verified identity claims (who built the agent, who authorized it, what it can do, how it pays). | $9.5M total (a16z CSX, Coinbase Ventures, Neuberger Berman). Partnered with Experian. |
| Experian Agent Trust | Human-to-agent binding: takes KYA tokens and enriches them against Experian's consumer and business data, issues a real-time risk score. Partners include Skyfire, Akamai, Visa, Cloudflare. | Enterprise incumbency. Launched April 2026. |
| Trulioo | Published KYA white paper. Extending existing KYB/KYC platform to cover agent identity verification. | Established identity verification vendor, 195 countries. |
| KnowYourAgent.xyz | Lightweight agent verification at checkout. Consumer-facing. | Early stage, narrow scope. |

Three distinct approaches are emerging:

1. **Business graph oracles** (Baselayer): verify the legal entity behind the
   agent via authoritative records. Answer: "is this business real and clean?"

2. **Agent credential issuers** (Skyfire, Clerk, AgentPass): issue signed tokens
   that assert what the agent is authorized to do on behalf of a verified human.
   Answer: "is this agent properly delegated?"

3. **Network trust stamps** (Experian, Visa TAP, Mastercard Agent Pay): large
   incumbents enriching agent identity with their existing risk data and network
   relationships. Answer: "does our network vouch for this counterparty?"

These three approaches are complementary, not competing. A production agentic
commerce stack needs all three: a business graph oracle to verify the entity,
a credential issuer to constrain the agent's authority, and a network trust
stamp to make the credential universally recognized. SupplyMind builds the
protocol layer that sits above all three: the agent-to-agent transaction flow
that consumes these trust signals and acts on them.

**Why this matters for SupplyMind:**
SupplyMind intentionally left this gap open. The prototype builds and operates
the transaction protocol stack (MCP, A2A (Agent-to-Agent), UCP (Universal Commerce Protocol), AP2 (Agentic Payment Protocol), ACP (Agentic Commerce Protocol)) and documents where
an external trust oracle would plug in. That gap, between cryptographic identity
and business entity verification, is where the business entity verification
market is building today. SupplyMind's architecture is a working prototype of
the transaction layer that consumes those trust signals.

---

## Phase 8: DNSid — Agent Ownership Registry (Done)

**Type:** Protocol
**Established by:** Identity Digital Innovation Labs (dnsid.ai), launched
April 27 2026. Linux Foundation Decentralized Trust member. Neutral governance.
**Adoption:** Very early. Launch-stage as of May 2026.
**Maturity:** Experimental. Brand new protocol with no production deployments
as of May 2026.

**Problem it solves:**
Cryptographic identity (Phase 6) proves a document was signed by a key. It does
not prove who owns the key or whether the agent using it is still authorized to
act. DNSid is the ownership registry: it anchors an agent's identifier to a DNS
domain, records the owner, and provides revocation. When an agent is compromised
or decommissioned, its DNSid handle is revoked and all downstream systems that
check before transacting will reject it.

This is the layer that transforms SupplyMind from autonomous to accountable.

**Dependencies and sequencing:**
Requires Phase 6 (secp256k1 + KYA (Know Your Agent)) — DNSid anchors the existing cryptographic
identity to a DNS domain and adds ownership and revocation on top. Phase 9
(signed mandates) requires DNSid to know who is signing the Intent Mandate.
Phase 11 (governance dashboard) audits by DNSid handle. Skipping Phase 8 means
every phase above it has no ownership accountability layer.

**Alternatives considered:**
- Pure did:web (no ownership registry) provides cryptographic identity without
  a revocation mechanism. It answers "was this signed by this key?" but not
  "does the key's owner still authorize this agent?"
- LoginID FIDO2/WebAuthn binds agent identity to biometric authentication,
  which is strong for human-controlled agents but adds friction for fully
  autonomous agents operating without human presence.
- Okta XAA + ID-JAG (Okta's agent identity framework) is enterprise-grade but
  tightly coupled to the Okta identity ecosystem — not suitable for an
  open, vendor-neutral stack.
- DNSid (Domain Name System identity) was the learning target for this phase. DNSid is vendor-neutral, an LF Decentralized Trust member, DNS-anchored (reusing existing infrastructure), and specifically
  designed for agent ownership rather than adapted from human identity patterns.

**Security loopholes to address in build:**

- [Identity] Resolution latency in the x402 critical path. Every x402
  micro-payment must resolve the counterparty's DNSid before firing. Mitigation:
  short-lived local cache with a TTL shorter than the revocation SLA.

- [Identity] Revocation lag. Between when an agent is compromised and when its
  DNSid is revoked, the compromised agent can still transact. Mitigation:
  reduce TTL on cached resolutions and implement push notification for
  revocation events.

- [Enforcement] Mock resolver must simulate failure modes. Resolution timeout,
  registry unavailable, revoked handle — a system that only handles the happy
  path will fail in production.

**Why this matters:**
DNSid is the missing link between cryptographic proof and enterprise trust. Every
phase above it becomes more meaningful when ownership is verifiable and revocable.
Without DNSid, you have a system that can prove it has a key; with DNSid, you
have a system that can prove who is accountable for that key.

---

## Phase 9: AP2 v0.2.0 — Signed Mandate Upgrade (Done)

**Type:** Protocol upgrade
**Announced:** Google I/O May 2026. 60+ partners including PayPal, Mastercard,
Amex, Klarna.
**Maturity:** Experimental. Announced May 2026, no production implementations yet.

**Problem it solves:**
The Phase 4 mandate is a runtime policy check in memory. AP2 v0.2.0 replaces it
with cryptographically signed Intent Mandates (human signs upfront using a
secp256k1 key -- in production this is a LoginID FIDO2 hardware-backed
biometric ceremony) and Cart Mandates (agent signs at purchase time, linked
back to Intent Mandate). Creates a tamper-proof audit trail from human intent
to payment execution.

**Dependencies and sequencing:**
Requires Phase 7 (secp256k1) for the signing infrastructure. Requires Phase 8
(DNSid, Domain Name System identity) for the vendor_dnsid field in Cart Mandates and for the DNSid gate that
must pass before a Cart Mandate is issued. Without Phase 9, the governance
dashboard (Phase 11) has no signed mandate records to audit.

**Alternatives considered:**
- Mastercard Verifiable Intent (Phase 14) creates a similar tamper-resistant
  audit trail from the card network side. The two are complementary: AP2
  governs the agent's internal spending policy; Verifiable Intent creates a
  network-level record visible to the card network and issuer.
- Clerk AgentPass handles task specification and approval at the identity
  provider level — it answers "who approved this task" rather than "what
  spending bounds apply." Together with AP2 v0.2.0, they would cover both
  task approval and spending governance.
- Mission-bound OAuth constrains an agent's OAuth token to a specific task
  scope, expiring when the task is complete. It addresses scoping more than
  it addresses spending bounds.

**Security loopholes to address in build:**

- [Approvals] Cart Mandate constraint validation must be atomic. The validator
  checking a Cart Mandate against its linked Intent Mandate must execute in
  the same transaction as the payment authorization. A race condition could
  allow a cart to be approved after the Intent Mandate expires or is revoked.

- [Approvals] Mandate linkage must be cryptographically verified. The
  links_to_intent_mandate field must be verified by resolving and checking the
  Intent Mandate signature, not just checking that a string ID exists.

**Why this matters:**
The autonomous-to-$345M payment risk is not solved by a policy check that exists
only in memory. It is solved by a cryptographic chain of custody that is
independently verifiable long after the transaction completes.

---

## Phase 10: Seller Authorization Manifest (Done)

**Type:** Novel spec (no existing standard -- borrows AP2 (Agentic Payment Protocol) v0.2.0 cryptographic pattern)
**Established by:** SupplyMind Phase 10. Proposed as companion standard to AP2.
**Maturity:** Experimental. No existing standard; SupplyMind is the reference implementation.

**Problem it solves:**
HTTPS gives browser commerce a cryptographic trust signal: the padlock in the URL
bar proves the server is operated by the named entity. Agentic and social commerce
remove the browser. When a human buys from within Claude, ChatGPT, or a TikTok
feed, there is no URL bar, no padlock, no SSL certificate visible to the human.
The interface navigates to the seller on the human's behalf with no machine-readable
signal to verify the seller is legitimate and the offer genuine.

Two concrete use cases that exist today (before autonomous buyer agents are common):

1. Chat-native commerce: human tells Claude "order 500 reams of paper." Claude
   finds a seller, presents a quote, completes the purchase inside the chat. The
   human needs to know: is this seller real, and is this price what their owner
   actually authorized?

2. Social commerce (TikTok, Instagram): human sees a product in a feed, taps buy,
   purchase completes inside the app. Same question without a browser to provide
   any trust signal.

The Seller Authorization Manifest is the replacement for HTTPS in these contexts:
a signed document created by the merchant's human operator before the selling agent
goes live. In production this signing step would be performed by LoginID FIDO2:
the operator's private key lives in hardware and a biometric gesture is required
to authorize the manifest. It states what the agent may sell, at what price ranges, with what
discount limits. The buyer agent or chat interface verifies the signed offer against
the manifest before presenting it to the human. Deviation fails at the transaction
boundary -- before the human confirms, not after money moves.

**What was built:**
- `src/identity/seller_manifest.py`: create_seller_manifest() (operator signs the
  authorization), create_signed_offer() (agent signs each quote against manifest),
  verify_signed_offer() (buyer-side runtime enforcement gate)
- Seller server: GET /.well-known/seller-manifest.json endpoint; quote responses
  include signed_offer with manifest embedded for full chain verification
- 12 tests: 9 unit + 3 integration

**Relationship to AP2:**
AP2 is buyer-side governance by design. It governs what a buyer agent can spend,
not what a seller agent can offer. The Seller Authorization Manifest borrows AP2's
cryptographic pattern (secp256k1-signed document, human operator key -- in
production a LoginID FIDO2 hardware-backed biometric ceremony -- agent
execution key) and applies it to the seller side. This is not AP2 -- it is a
novel companion spec that fills a gap AP2 does not address.

**Dependencies and sequencing:**
Requires Phase 7 (secp256k1) for the signing infrastructure. Requires Phase 9
(AP2 v0.2.0) as the buyer-side complement -- the two together give Clerk's full
four-question coverage on both sides. Phase 11 (governance dashboard) aggregates
both buyer and seller signed artifacts into a single audit view.

**Merchant friction and deployment strategy:**
Three-tier deployment: Approach 1 (price buffer policy, no-code, zero ongoing
friction -- right launch config), Approach 2 (catalog-sync manifest, one-tap
mobile confirm for mid-market), Approach 3 (ERP/PIM MCP (Model Context Protocol) integration, LoginID
biometric on live system data -- enterprise tier and strongest LoginID
differentiation). See LoginID-Firmly eval.md for full analysis.

**Security loopholes to address:**

- [Enforcement] Manifest must be versioned. If a merchant updates pricing, the
  old manifest must not be accepted for new offers. Manifest ID must be
  timestamp-bound or include an expiry field in production.

- [Enforcement] Offer replay attack: a signed offer is valid until rejected.
  Production must include a nonce or timestamp in the offer that expires quickly,
  preventing a buyer from replaying an old offer at an old price.

- [Scoping] Price buffer width is a policy decision. A buffer that is too wide
  (±50%) defeats the purpose of the manifest. Production should enforce a maximum
  buffer width as a platform-level governance parameter.

**Why this matters:**
The padlock is the most trusted security signal in consumer computing history --
so trusted it is invisible. Removing it without a replacement is not an acceptable
security posture for agentic or social commerce at scale. The Seller Authorization
Manifest is the structural replacement: machine-readable, cryptographically signed,
independently verifiable by any chat interface or buyer agent without a browser.

---

## Phase 11: Governance and Audit Dashboard (Done)

**Type:** Application (implements DNSid (Domain Name System identity), AP2 (Agentic Payment Protocol), x402, NANDA (Networked Agents and Decentralized Architecture) as data sources)
**Maturity:** N/A (SupplyMind-specific implementation).

**Problem it solves:**
A CISO approving autonomous procurement needs to answer four questions in one
place: who are my agents and who owns them? What are they authorized to spend?
What have they actually spent? Has anything suspicious happened?

**Dependencies and sequencing:**
Requires Phases 8, 9, and 10 to have meaningful data to display. Without DNSid
handles, the agent registry has no ownership data. Without signed mandates and
seller manifests, the mandate and offer ledgers have no cryptographic records.
Phase 15 (fraud detection) feeds anomalies into this dashboard. The dashboard is the visibility layer
for every security investment made in previous phases.

**Alternatives considered:**
- Web UI instead of CLI: adds development effort without changing the underlying
  data model. CLI first is the right call — the data model and query patterns
  are established in the CLI, and the web UI is a rendering concern.
- Third-party observability tools (Datadog, Grafana) handle metrics and logs but
  do not understand DNSid handles, mandate structures, or agentic commerce
  semantics. A custom dashboard is the only option for domain-specific audit.

**What was built:**
- `src/governance/dashboard.py`: FastAPI server on port 8085. Six endpoints:
  GET /governance/agents (Identity), /governance/seller-manifests (Scoping seller),
  /governance/intent-mandates (Scoping buyer), /governance/cart-mandates (Approvals),
  /governance/signed-offers (Enforcement), /governance/summary (CISO single-screen),
  /governance/audit-trail (durable log), /governance/protocols (Phase 12 protocol breakdown)
- `src/governance/event_log.py`: append-only JSONL audit log at logs/audit.jsonl.
  Every significant event (agent registration, revocation, manifest signing, mandate
  creation, transaction completion) is written as it happens. Persists across restarts.
- Dashboard reads live data from seller server via HTTP endpoints added to seller:
  GET /governance/data/agents, /manifests, /intent-mandates, /cart-mandates, /signed-offers
- Falls back to in-process in-memory reads when seller server is unreachable (test mode)

**Log file format (logs/audit.jsonl):**
One JSON object per line. Example:
  {"ts": "2026-06-02T20:12:07Z", "layer": "Identity", "event": "agent_registered",
   "entity": "dnsid://supplymind.localhost/agents/seller-001",
   "operator": "supplymind.localhost", "detail": "agent_id=seller-001"}

**Why this matters:**
The governance dashboard is not a Phase 11 add-on. It is the artifact that makes
every phase before it auditable. Without it, the security properties of DNSid,
signed mandates, and network credentials exist in logs that no one reads.
With the durable log, every event is written to disk as it happens -- a CISO can
open logs/audit.jsonl in any text editor and read the complete history of every
agent, every authorization, and every transaction the system has ever processed.

---

## Phase 12: ACP — Agentic Commerce Protocol (Done)

**Type:** Protocol
**Established by:** OpenAI and Stripe (September 2025). Apache 2.0.
**Adoption:** Live at Etsy and expanding to 1M+ Shopify merchants. 7x retail
sales uplift for ACP-integrated sellers during Cyber Week 2025.
**Maturity:** Maturing. Live production deployments, active spec development,
strong ecosystem traction in B2C.

**Problem it solves:**
A buyer agent built on GPT-4o speaks ACP, not UCP (Universal Commerce Protocol). SupplyMind sellers currently
only speak UCP. Adding ACP makes the seller reachable from any commerce AI
regardless of which LLM powers the buyer. Merchants supporting both see ~40%
more agentic traffic than single-protocol merchants.

**Dependencies and sequencing:**
Requires UCP (Phase 2) to already exist — the protocol router needs a UCP
handler to route from before an ACP handler can be added alongside it.
The AP2 (Agentic Payment Protocol) mandate engine (Phase 4) sits above both protocols and enforces the
same spending policy regardless of which checkout protocol the buyer used.

**Alternatives considered:**
- UCP only: simpler, but partitions the seller from all non-Gemini buyer agents.
  Single-protocol lock-in in a two-protocol world costs approximately 40%
  of accessible agentic traffic based on current data.
- ACP only: stronger B2C traction but weaker B2B semantic catalog support.
  UCP's JSON-LD and schema.org vocabulary is better suited to SupplyMind's
  B2B procurement use case.
- Both ACP (Agentic Commerce Protocol) and UCP (Universal Commerce Protocol) were learning targets for this phase, implemented via a protocol router.

**Security loopholes:**

- [Identity] Protocol router must not bypass DNSid (Domain Name System identity) gates. A buyer coming in
  via ACP must be subject to the same DNSid ownership verification as a UCP
  buyer. The router must apply identity checks before routing, not after.

- [Scoping] ACP and UCP may expose different catalog fields. The router must
  ensure that a buyer cannot access more catalog data via one protocol than
  the other. Schema normalization is required before routing.

**What was built:**
- `src/seller_agent/protocol_router.py`: normalize_acp() and normalize_ucp_task()
  convert either wire format to NormalizedOrder. Single shared pipeline for all protocols.
- POST /acp/v1/checkout: new endpoint for GPT-4o and Stripe-based buyer agents.
  Same DNSid and Cart Mandate gates as UCP -- protocol cannot bypass identity checks.
- protocol_of_record field ("acp" or "ucp") in every task result and governance audit trail.
- GET /governance/protocols: dashboard endpoint showing protocol breakdown per transaction.
- 9 tests: 2 unit (router normalization) + 7 integration.

**Security invariant implemented:**
DNSid and Cart Mandate gates are applied in _apply_gates() BEFORE routing to the
order execution pipeline. A buyer agent using ACP cannot bypass any gate that a
UCP buyer would face. The protocol is a transport choice, not a trust level.

**Why this matters:**
Single-protocol sellers are partitioned from a large portion of agentic traffic.
The protocol router makes SupplyMind protocol-agnostic at the checkout layer
while keeping the payment governance layer unified.

---

## Phase 12.5: Universal Cart (Done)

**Type:** Protocol
**Established by:** Google (2026). Separate from UCP (Universal Commerce Protocol).
**Maturity:** Experimental. Announced 2026; no reference implementation yet.

**Problem it solves:**
Every prior phase treats checkout as a stateless event. The buyer agent
discovers, queries, mandates, and pays in a single session. There is no
persistent cart object that survives between turns, accumulates items across
sellers, or hands structured state to the checkout session. For single-item
procurement this is acceptable. For multi-item, multi-session, or multi-seller
B2B orders it breaks: the buyer agent must rebuild context from scratch on
every turn.

Universal Cart adds a durable cart state layer. A cart is created once per
procurement event, accumulates items across agent turns, is anchored to the
buyer agent's DID (Decentralized Identifier), and is converted to a UCP checkout session at the checkout
step.

**What it adds to the stack:**
Universal Cart is the first protocol in SupplyMind that explicitly models
transaction state as a first-class object. Previous phases model events
(mandate created, payment executed, agent registered). Universal Cart models
a thing that persists and changes over time. This has downstream effects on
every layer above it:

- AP2 (Agentic Payment Protocol) mandate enforcement gains a full cart manifest (all items, total value,
  all sellers) rather than enforcing per-item. The mandate can now block a
  cart whose total exceeds the mandate limit even if each individual item
  is within bounds.
- Visa TAP (Trusted Agent Protocol) and Mastercard Agent Pay (Phase 14) gain a cart ID as the
  transaction anchor rather than a bare payment call. Network credentials
  can be bound to a specific cart, not just a payment amount.
- Fraud detection (Phase 15) gains cart history as a signal. Velocity checks
  can operate on cart add events, not just payment events.
- Governance audit trail (Phase 11) gains cart lifecycle events alongside
  mandate and payment events.

**Clerk's four-question lens:**

- Identity: cart is anchored to buyer_did (Phase 7 secp256k1 identity).
  A cart cannot be checked out by an agent with a different DID than the one
  that created it. Strengthens Identity.
- Scoping: AP2 mandate can now enforce against full cart value rather than
  per-item. Strengthens Scoping.
- Approvals: NOTIFY-tier human approval now presents a full cart manifest,
  not a single line item. Strengthens Approvals.
- Enforcement: no change at this phase. check_mandate() still runs inside
  the agent process boundary. Phase 14 network credentials begin to address
  independent enforcement.

**Dependencies and sequencing:**
Requires Phase 12 (UCP checkout sessions) -- checkout_cart() converts the
cart to a UCP checkout session. Requires Phase 7 (buyer_did) -- cart is
identity-anchored. Phase 13 wallet layer gains a cart-triggered checkout
path (checkout_cart calls the wallet's pay() rather than invoking it
directly). Phase 14 network credentials should bind to cart_id as the
transaction anchor.

**Alternatives considered:**

- Session-scoped cart (in-memory, not persistent): simpler but defeats the
  purpose. If the agent restarts or pauses between turns, the cart is lost.
  SQLite persistence is the minimum viable durability.
- Single-seller cart only: simpler model but limits B2B procurement realism.
  SupplyMind implements multi-seller cart (items carry seller_did) to
  reflect real procurement where a buyer may source from multiple vendors
  in one order.
- Embedding cart state in the AP2 mandate: philosophically wrong. The
  mandate governs spending policy. The cart is the transaction state.
  Conflating them makes both harder to audit.

**What was built:**

- `src/cart_server/cart.py`: Cart and CartItem data models, SQLite backend
  at data/carts.db. Fields: cart_id (UUID), buyer_did, items (product_id,
  quantity, unit_price, seller_did, seller_endpoint), status
  (open/checked_out/abandoned), created_at, updated_at.
- `src/cart_server/server.py`: FastMCP server exposing four tools:
  add_to_cart, view_cart, remove_from_cart, checkout_cart.
- Seller agent: four cart endpoints added to FastAPI server:
  POST /cart/v1/carts, GET /cart/v1/carts/{cart_id},
  PATCH /cart/v1/carts/{cart_id}, POST /cart/v1/carts/{cart_id}/checkout.
- Buyer agent: updated to call add_to_cart before checkout rather than
  going directly to UCP checkout session.
- Governance audit trail: cart lifecycle events (created, item_added,
  checked_out) written to logs/audit.jsonl.
- `tests/test_phase12_5.py`: create cart, add items, view cart, checkout
  via UCP, verify audit trail entries.

**Security loopholes to address:**

- [Identity] Cart ownership must be verified at checkout. An agent must
  present a signed proof that it is the buyer_did that created the cart.
  Without this, any agent that knows a cart_id can check it out.

- [Scoping] Cart total must be computed server-side, not trusted from the
  client. If the buyer agent sends a checkout request with a tampered total,
  the seller must recompute from line items.

- [Enforcement] Cart status transitions (open to checked_out) must be atomic.
  A race condition where two agents check out the same cart is a double-spend
  risk. SQLite row-level locking or a status check-and-set must be atomic.

**Why this matters:**
Universal Cart is the protocol that makes multi-turn, multi-item, multi-seller
agentic procurement possible without rebuilding context from scratch on every
turn. The industry announcement of Universal Cart as a separate protocol from
UCP confirms that stateless checkout is a recognized limitation of the current
agentic commerce stack. Building it before Phase 14 network credentials gives
every downstream phase a richer transaction object to work with.

**Industry signal:**
Google's decision to separate Universal Cart from UCP rather than extending
UCP reflects a clean architectural boundary: UCP is a checkout protocol
(stateless, single-seller, single-session). Universal Cart is a state
management protocol (stateful, multi-seller, multi-session). SupplyMind's
implementation follows this boundary: checkout_cart() converts cart state
to a UCP checkout session at the handoff point, but neither protocol knows
about the other's internals.

---

## Phase 13: Agent Wallet Layer (13a Done -- mock; 13b optional with real APIs)

**Type:** Implementation (Stripe Link Agent Wallet + Coinbase/Base MCP (Model Context Protocol))
**Maturity:** Maturing. Stripe Link and Coinbase wallets are production-grade;
Base MCP (launched May 26 2026) is early.

**Problem it solves:**
The current payment rails are simulated. Phase 12 introduces real wallet
infrastructure: Stripe Link for fiat (one-time virtual card per agent task)
and Coinbase Agentic Wallet for stablecoin (USDC, programmable spending
policies, non-custodial identity anchored to DNSid (Domain Name System identity)).

**Dependencies and sequencing:**
Requires AP2 (Agentic Payment Protocol) mandates (Phase 4/9) to be in place before real money flows —
a funded wallet without a spending policy is a liability. Real x402 on-chain
settlement requires the Coinbase/Base wallet provisioned in Phase 13. Skipping
Phase 13 means there is no funded wallet to draw from.

**Alternatives considered:**
- Circle Programmable Wallets are the stablecoin wallet alternative to
  Coinbase — both support USDC on multiple chains. Circle has stronger
  enterprise payment credentials and existing integration in SupplyMind's
  earlier simulation code. Coinbase/Base MCP is chosen for Phase 13 because
  of the native Claude integration via Base MCP.
- PayPal agent wallet is in early development and targets consumer use cases
  more than B2B procurement.
- Custodial vs. non-custodial is the key design decision: custodial (Stripe
  holds the funds) is simpler but creates counterparty risk; non-custodial
  (Coinbase, agent controls the key) is more complex but aligns with the
  DNSid ownership model.

**LoginID's role:**
Financial regulators require KYC (Know Your Customer) on wallet owners. When an
agent wallet is provisioned -- whether Stripe Link or Coinbase USDC -- someone
must prove they are the human owner who authorized it. Without this, an autonomous
agent could provision a wallet and move money with no human accountable.

LoginID is the provisioning ceremony. The `provision_wallet()` function requires
an `operator_id` parameter -- the verified human who authorized wallet creation.
In production this is a LoginID FIDO2 biometric event: the CFO or procurement
manager performs a Touch ID or hardware key gesture, LoginID returns a signed
attestation, and that attestation is stored as the `provisioned_by` field in the
wallet record. The wallet cannot be created without it.

This is LoginID's clearest product in the agentic commerce stack: every regulated
financial institution will require a human accountability record before allowing
an autonomous agent to hold and spend funds. LoginID produces that record.
The `operator_id` field in every wallet record is the audit artifact -- it proves
which human, verified by hardware biometric, authorized this agent to handle money.

In the SupplyMind mock, `operator_id` is a string ("cfo@supplymind.localhost").
In production, it is a LoginID attestation object with a FIDO2 credential ID,
timestamp, and cryptographic proof. The field is there in the schema precisely
so the production swap is a one-line change.

**Why this matters:**
Real wallets introduce real financial risk. The security properties of all
previous phases exist precisely so that when real money flows, it flows within
auditable, policy-constrained boundaries.

**What was built (Phase 13a -- high-fidelity mock):**
- `src/payment_server/wallet.py`: WALLETS dict, two rails (stripe_link fiat /
  coinbase_usdc stablecoin). Address formats match real APIs: pm_test_* for Stripe,
  0x* for Coinbase. execute_payment() debits buyer, credits seller, enforces mandate
  per-tx limit, calls record_spend(), logs to audit trail. All return schemas mirror
  real Stripe PaymentIntent and Coinbase transaction response formats.
- `src/payment_server/wallet_seed.py`: seeds buyer (1000 USDC + 5000 USD fiat)
  and seller (0 USDC receives payments) wallets at startup via LoginID-hook operator.
- Seller server: execute_payment() called in _build_task_result(); payment_result
  added to every task result; GET /wallet/balance and GET /governance/data/wallets
  endpoints added.
- Governance dashboard: GET /governance/wallets endpoint; wallet_layer_active in
  summary; wallet events in audit trail.
- 11 tests: 6 unit (provision, payment, insufficient funds, mandate limit, history)
  + 5 integration.

**Phase 13b (optional -- requires free account creation):**
Wire up real test APIs. Both are free sandboxes:
- Stripe: sign up at stripe.com, get sk_test_... key, add to .env. Replace
  _mock_stripe_address() with real Stripe PaymentMethod create call.
- Coinbase: sign up at coinbase.com/developer-platform, get CDP API key, add to .env.
  Replace _mock_coinbase_address() with real AgentKit wallet.create() on Base Sepolia.
  Get test USDC from faucet.base.org (free, 2 minutes).
The function signatures and return schemas are identical -- only the implementation
of the two mock address functions changes.

---

## Phase 14: Network Credential Layer — Visa TAP + Mastercard Agent Pay (Done)

**Type:** Protocol (Visa TAP (Trusted Agent Protocol)) + Framework (Mastercard Agent Pay)
**Established by:** Visa TAP (October 2025, RFC 9421). Mastercard Agent Pay
(April 2025) + Verifiable Intent (March 2026, with Google, Fiserv, IBM).
**Adoption:** Visa TAP live at Adyen, Stripe, Worldpay. Mastercard full US
coverage November 2025.
**Maturity:** Maturing. Both are live with major payment processors, though
direct merchant integration is still rolling out.

**Problem it solves:**
Two distinct problems:

Visa TAP: how does a merchant distinguish a legitimate AI agent from a malicious
bot? Adds a cryptographically signed HTTP header to every agent-initiated
transaction, verifiable against Visa's public key directory using RFC 9421.

Mastercard Agent Pay: how does an agent transact using a card without holding
the raw card number? Agentic Tokens bound to a specific agent, merchant scope,
and consent policy — unusable outside those bounds.

Mastercard Verifiable Intent: creates a tamper-resistant, cryptographically
signed record linking the consumer's identity, their specific instructions,
and the transaction outcome for audit and dispute resolution.

**Dependencies and sequencing:**
Requires Phase 8 (DNSid, Domain Name System identity) — Visa TAP and Mastercard Agentic Tokens are bound
to a specific agent identity; DNSid provides the ownership layer that makes
that binding meaningful. Requires Phase 13 (real wallets) — network credentials
are meaningless without a real payment instrument behind them.

**Alternatives considered:**
- Visa TAP and Mastercard Agent Pay are not mutually exclusive. Full network
  coverage requires both, since issuer acceptance depends on which network
  the cardholder's account runs on.
- Relying on AP2 (Agentic Payment Protocol) Mandates alone (no network credential) is viable for
  stablecoin-only deployments but is not acceptable to any bank or credit
  union that processes card transactions.
- SupplyMind implements both because the enterprise compliance stack requires
  both: DNSid (who owns it) + Visa TAP (authorized to pay) + AP2 Intent Mandate
  (spending bounds) = the complete answer to regulators and CISOs.

**Security loopholes:**

- [Identity] Visa TAP: credential binding must reference DNSid. The TAP
  credential identifies the agent operator's public key directory. Without
  binding to DNSid, a credential can be issued to an agent that is later
  revoked from DNSid — the revocation is not reflected in the TAP credential
  until it expires.

- [Approvals] Mastercard Verifiable Intent and AP2 Intent Mandates cover the
  same conceptual ground from different angles. They must be consistent: if
  the Intent Mandate says max $500 and the Verifiable Intent record says the
  consumer approved $1000, there is a conflict that needs a defined resolution
  policy.

**What was built:**

- `src/identity/visa_tap.py`: `issue_tap_credential()` -- signs a credential
  document (schema: visa-tap:v1.0) binding agent_did, dnsid_handle, merchant_did,
  cart_id, amount, and expiry to a secp256k1 signature. `verify_tap_credential()`
  -- checks signature, expiry, and DNSid revocation status.
  `credential_to_header()` / `credential_from_header()` -- base64 encode/decode
  for the TAP-Agent-Credential HTTP header.

- `src/identity/mastercard_agent_pay.py`: `issue_agentic_token()` -- issues a
  scoped Agentic Token (schema: mc-agent-pay:agentic-token:v1.0) bound to agent,
  merchant, max amount, and consent scope. `verify_agentic_token()` -- checks
  signature, expiry, merchant scope binding, amount limit, and DNSid revocation.
  `create_verifiable_intent()` -- signed record linking human instruction, token,
  cart, amount, and outcome (schema: mc-agent-pay:verifiable-intent:v1.0).
  `verify_verifiable_intent()` -- cryptographic signature check.

- Seller agent: `_apply_gates()` extended to accept and verify optional
  TAP-Agent-Credential and MC-Agent-Token-Id headers. Both gates are additive
  (absent = not verified, present + valid = verified). The task result includes
  `tap_verified` and `mc_token_verified` fields alongside the existing
  `buyer_dnsid_verified` and `cart_mandate_verified`.

- Governance dashboard: `GET /governance/network-credentials` -- lists all issued
  TAP credentials, MC Agentic Tokens, and Verifiable Intents with proof status.
  `GET /governance/summary` updated with `network_credentials_active` flag.

- Audit log: `tap_credential_issued`, `tap_credential_verified`,
  `mc_agentic_token_issued`, `mc_verifiable_intent_created` events written to
  logs/audit.jsonl via the existing event log infrastructure.

- 21 tests: 15 unit (issue, verify, tamper, expiry, revocation, roundtrip for
  both protocols) + 4 HTTP integration (valid TAP header, invalid TAP header,
  valid MC token, unknown MC token) + 2 governance integration.

**Trust chain after Phase 14:**

```
Human biometric (LoginID)      --> signs Intent Mandate (AP2 v0.2.0)
Intent Mandate                 --> constrains Cart Mandate
Agent key (Phase 7)            --> signs Cart Mandate + TAP credential + MC token
DNSid handle (Phase 8)         --> anchors all credentials to domain ownership
Visa TAP credential            --> network-level agent identity per transaction
MC Agentic Token               --> scoped payment token (agent + merchant + consent)
MC Verifiable Intent           --> tamper-resistant outcome record
Seller (_apply_gates)          --> verifies all gates before any payment
Governance dashboard           --> aggregates all trust signals in one view
```

**TAP vs. Mastercard Agent Pay -- analogues and differences:**

The analogous pairs are:

| Visa TAP component | Mastercard Agent Pay component | What it proves |
|---|---|---|
| TAP Credential | Agentic Token | Agent was authorized by a human cardholder |
| Human Authorization Token (HAT) | Verifiable Intent | Human explicitly instructed this purchase |
| RFC 9421 HTTP Message Signature | Agentic Token signature (Mastercard-signed) | Request was not tampered with in transit |

The structural difference is in *where enforcement lives*:

Visa TAP is a per-request identity proof. The merchant verifies a signed HTTP
header on every transaction. It answers "is this a legitimate agent?" at the
request boundary. TAP does not define a standing policy for what the agent is
allowed to buy -- that is the operator's responsibility to encode in the
credential at issuance.

Mastercard adds the Agent Commerce Authorization (ACA): a network-level policy
layer that lets issuers and merchants define permissible categories, merchants,
and amount limits before any transaction attempt. An agent token can be scoped
to "office supplies only, max $500, Staples and Amazon only" at the time the
human grants consent. This is the closest network-level equivalent to AP2's
Intent Mandate -- spending bounds enforced by the network, not just the seller.

In short: TAP proves identity per request. Mastercard proves identity plus
enforces spending policy via the network. They are not redundant. An enterprise
stack needs both: TAP for network-wide agent authentication (Visa rails), MC
Agent Pay for network-enforced scope limits (Mastercard rails).

**Why this matters:**
Financial institution deployment requires network-level credentials. A bank
cannot accept autonomous payments from an agent identified only by a self-issued
DID (Decentralized Identifier) and a local mandate. Visa TAP and Mastercard Agent Pay are the credentials
that existing financial infrastructure recognizes.

---

## Phase 15: Fraud and Bot Detection (Planned)

**Type:** Implementation (Stripe Radar + DNSid (Domain Name System identity) rate limiting)
**Maturity:** Experimental (DNSid-anchored rate limiting is novel).
Maturing (Stripe Radar is production-grade).

**Problem it solves:**
MCP (Model Context Protocol) traffic increased 50x in one week after Anthropic connector expansion.
Seller agents exposed to the open web receive traffic from legitimate buyer
agents and from automated scanners, scrapers, and bots.

**Dependencies and sequencing:**
Requires Phase 8 (DNSid) — rate limiting and traffic classification are anchored
to DNSid handles. Without DNSid, rate limiting must fall back to IP addresses,
which are trivially rotated. Requires Phase 11 (governance dashboard) as the
surface where anomalies are surfaced.

**Alternatives considered:**
- Cloudflare Bot Management provides sophisticated bot detection at the network
  edge but does not understand DNSid handles or agentic commerce semantics —
  it would treat a slow legitimate agent the same as a bot.
- Custom rate limiting without DNSid anchoring is weak because bots rotate IPs.
  DNSid anchoring means a rate-limited agent cannot simply reconnect from a
  new IP — it must present a new valid DNSid handle.

**Why this matters:**
Fraud detection is the operational layer that makes the security architecture
real rather than theoretical. The governance dashboard becomes the monitoring
surface for anomalies surfaced here.

---

## Phase 16: Stablecoin Settlement — x402 Foundation + AWS AgentCore (Planned)

**Type:** Implementation (x402 Linux Foundation spec + AWS Bedrock AgentCore)
**Established by:** x402 Foundation launched April 2 2026. AWS AgentCore
Payments launched in preview May 7 2026 (Coinbase + Stripe).
**Maturity:** Experimental. x402 Foundation is new; AWS AgentCore Payments
is in preview as of May 2026.

**Problem it solves:**
The current x402 path accepts any non-empty payment header as proof. Phase 16
replaces this with real on-chain verification via the x402 Linux Foundation spec
and optionally routes through AWS AgentCore Payments as the managed execution layer.

**Dependencies and sequencing:**
Requires Phase 13 (funded wallet on Base) — x402 on Base requires USDC in the
buyer's Coinbase wallet. Requires Phase 8 (DNSid, Domain Name System identity, gates on x402 path) — real
settlement should not proceed without ownership verification. Requires Phase 3
(x402 protocol skeleton) — Phase 16 upgrades the existing path rather than
building from scratch.

**Alternatives considered:**
- Self-hosted x402 verification: query Base directly for transaction
  confirmation. Full control, no third-party dependency, but requires
  maintaining blockchain RPC infrastructure.
- AWS AgentCore Payments: managed service that abstracts x402 + Coinbase/Stripe
  rails. Simpler to operate but introduces AWS dependency and preview-stage
  reliability risk.
- The payment decision tree governs the choice at runtime: micropayments go
  x402 USDC; small procurement goes AP2 (Agentic Payment Protocol) + Stripe Link; large procurement
  goes AP2 + Visa TAP (Trusted Agent Protocol)/MC Agent Pay. The decision is by transaction size, not
  protocol preference.

**Why this matters:**
Phase 16 closes the loop opened in Phase 3. The x402 protocol was always designed
to verify on-chain; it was simulated in early phases to make the architecture
understandable without requiring testnet infrastructure. Real settlement is the
final step that makes SupplyMind a working financial system rather than a
simulation of one.

---

## Full Protocol and Framework Summary

| # | Name | Type | Established by | Layer | Maturity | Status |
|---|------|------|---------------|-------|----------|--------|
| 1 | MCP (Model Context Protocol) | Protocol | Anthropic / LF | Agent-to-tool | Production stable | Done |
| 2 | UCP (Universal Commerce Protocol) | Protocol | Google + coalition | Catalog + checkout | Maturing | Done |
| 3 | A2A (Agent-to-Agent) | Protocol | Google DeepMind / LF | Agent discovery + tasks | Maturing | Done |
| 3 | x402 | Protocol | Coinbase / LF | Micro-payment | Maturing | Simulated |
| 4 | AP2 (Agentic Payment Protocol) v0.1 | Protocol | Google | Payment governance | Maturing | Done |
| 4 | ACF (Agentic Commerce Framework) | Framework | Vincent Dorange | Tiered autonomy | Experimental | Done |
| 4 | MPP (Machine Payments Protocol) | Protocol | Stripe + Tempo | Multi-rail settlement | Experimental | Simulated |
| 5 | (partial) | | | Protocol reflection, 2nd seller | | Partial |
| 6 | NANDA (Networked Agents and Decentralized Architecture) | Protocol | Project NANDA | Decentralized registry | Experimental | Done (localhost) |
| 7 | KYA (Know Your Agent) + secp256k1 | Framework + Protocol | W3C + industry | Cryptographic identity | Maturing / Experimental | Done |
| 8 | DNSid (Domain Name System identity) | Protocol | Identity Digital | Ownership + revocation | Experimental | Done |
| 9 | AP2 v0.2.0 | Protocol | Google | Signed mandates | Experimental | Done |
| 10 | Seller Auth Manifest | Application | SupplyMind | Seller-side governance | N/A | Done |
| 11 | Governance Dashboard | Application | SupplyMind | Audit + oversight | N/A | Done |
| 12 | ACP (Agentic Commerce Protocol) | Protocol | OpenAI + Stripe | Multi-protocol checkout | Maturing | Done |
| 12.5 | Universal Cart | Protocol | Google | Cart state layer | Experimental | Done |
| 13 | Stripe Link + Coinbase | Implementation | Stripe, Coinbase | Agent wallet layer | Maturing | Done (13a mock) |
| 14 | Visa TAP (Trusted Agent Protocol) + MC Agent Pay | Protocol + Framework | Visa, Mastercard | Network credentials | Maturing | Done |
| 15 | Stripe Radar + DNSid | Implementation | Stripe + SupplyMind | Fraud detection | Experimental | Planned |
| 16 | x402 (LF) + AWS AgentCore | Protocol + Managed infra | LF + AWS | Real settlement | Experimental | Planned |

---

## What SupplyMind Leaves Open

After all 15 phases are complete, four questions from Clerk's agentic auth
analysis are answered to varying degrees. This section is an honest accounting
of what remains unresolved.

### Identity: largely answered

After Phase 8, SupplyMind can answer who an agent is (secp256k1 + KYA (Know Your Agent)), who
owns it (DNSid, Domain Name System identity), and whether its owner vouches for it (DNSid registry). What
remains open: identity is not enforced at the MCP (Model Context Protocol) tool call level. Individual
tool calls carry no signed caller identity. An agent with a valid DNSid can
call any MCP tool on a server it can reach. Closing this gap requires per-call
auth at the MCP transport layer — something MCP Auth (Linux Foundation) and
AgentPass (Clerk) are working toward but SupplyMind does not implement.

### Scoping: partially answered

After Phase 9, SupplyMind can constrain what an agent spends via AP2 (Agentic Payment Protocol) mandate,
against which vendors (approved list + DNSid gate), and within what ACF (Agentic Commerce Framework) tier
thresholds. Phase 12.5 (Universal Cart) partially extends this: AP2 mandate
enforcement now operates against the full cart value rather than per-item,
closing the gap where a cart of many small items could exceed the intended
total while each individual item passed the per-item check. What remains open:
scoping is defined by amount and vendor, not by task. An agent operating
within its spending mandate can still purchase categories of goods not
intended by the human. Mission-bound OAuth and task-scoped credentials
(Clerk AgentPass) would close this gap by binding the agent's authorization
to a specific task description, not just a spending bound.

### Approvals: partially answered

After Phase 9, SupplyMind has a signed Intent Mandate (human approves the
policy upfront) and a Cart Mandate (agent locks the cart before payment).
What remains open: real-time approval escalation for edge cases. If a
purchase falls within mandate bounds but the human would want to know about it
(an unusual vendor, an unexpected item), there is no mechanism for the agent
to request an out-of-band approval. The NOTIFY tier logs a notification but
does not create a channel for the human to respond in real time without
stopping the agent entirely.

### Enforcement: the weakest layer

After Phases 4 and 8, SupplyMind enforces spending policy via check_mandate()
in the payment server and via DNSid gates before payment execution. What remains
open and is the most significant gap: nothing prevents a compromised agent
process from bypassing check_mandate() entirely. The enforcement is inside the
agent's own process boundary. Real enforcement requires the receiving service
to independently verify that the task was scoped and approved before accepting
the request — regardless of what the agent claims about itself. This is what
AgentPass (Clerk), MCP Auth (Linux Foundation), and AAuth (Dick Hardt) are
building: enforcement engines that sit outside the agent process and verify
task authorization in real time.

SupplyMind does not build an enforcement engine. This is the honest state of
the art across most of the industry in mid-2026: identity and governance
infrastructure are maturing rapidly; real-time enforcement independent of the
agent process is the frontier.

### The summary

Clerk's three keys to agent proliferation are task specification, approval
mechanism, and enforcement engine. SupplyMind builds a strong approval mechanism
(signed mandates) and partial task specification (mandate constraints). The
enforcement engine — independent real-time verification that the agent is doing
only what was approved — is the remaining gap. Naming it honestly is the first
step toward building it.

---

## Strategic Context: ICC, Firmly Connect, and the Identity Layer Gap (June 2026)

### Visa ICC vs. Firmly Connect

Visa Intelligent Commerce Connect (ICC, announced April 8, 2026) is a single
merchant endpoint that routes between TAP, MPP, ACP, and UCP simultaneously.
Merchants connect once; ICC handles protocol detection and translation.

Firmly Connect (launched March 2026) does the same thing: no-code merchant
onboarding, protocol abstraction, single integration point for any agent channel.

Architecturally they are equivalent at the protocol translation layer. In a
production system, replacing SupplyMind's manual protocol routing in the seller
agent with either ICC or Firmly Connect would produce the same result: the
seller agent exposes one endpoint, protocol handling disappears from application
code, and the buyer agent negotiates protocol with the aggregator rather than
with the seller directly.

What SupplyMind builds manually across Phases 2-12 — UCP catalog serving, AP2
mandate verification, ACP checkout handling, x402 micropayment response — is
exactly what ICC and Firmly Connect abstract away in production. Building it
manually is the learning value. Skipping it would mean understanding none of
the protocols underneath.

### The competitive tension

ICC commoditizes the protocol aggregation layer. Visa can bundle it at zero
marginal cost to merchants who already run on Visa infrastructure. Firmly
Connect's only differentiator at that layer is network neutrality — it is not
owned by a network that has a stake in which credential wins.

But network neutrality is a thin moat once ICC is good enough. The durable
differentiation is the identity layer, which neither ICC nor Firmly Connect
currently includes.

### The identity layer: what Firmly + LoginID adds

Firmly Connect today is protocol translation only. It does not include:

- Firmly ID: subdomain identity registry for human-owned agents (agent.firmly.ai/[id])
- DNSid integration: DNS-anchored ownership proof for business-owned agents
- LoginID FIDO2 passkey binding: ties mandate creation to a biometric hardware event, making mandates legally defensible and non-repudiable
- AP2 v0.2.0 signed mandate attestation: the human's authorization is cryptographically bound to their LoginID credential
- Seller Authorization Manifest: merchant-signed scope boundaries verifiable by any buyer agent via DNSid

The proposal (documented in docs/firmly_loginid_deck_final.html) is that Firmly
and LoginID build this identity layer on top of Firmly Connect. The resulting
stack answers all four of Clerk's agentic auth questions:

| Question | Answer |
|----------|--------|
| Identity | Firmly ID (humans) + DNSid (businesses) + LoginID passkey binding |
| Scoping | AP2 v0.2.0 signed mandate: amount, vendor, category, time window |
| Approvals | LoginID FIDO2 event at mandate creation: hardware-attested, non-repudiable |
| Enforcement | Firmly registry for revocation + Seller Authorization Manifest at session start |

ICC cannot replicate this without building a competing credential ecosystem,
competing merchant adoption, and a human enrollment network. That is the
structural barrier the proposal identifies.

### SupplyMind as proof of implementability

Every component of the proposed Firmly + LoginID identity stack has a working
analog in SupplyMind:

| Proposed component | SupplyMind analog | Phase |
|---|---|---|
| DNSid agent ownership anchor | dnsid_registry_seed.py, DNSid gate in payment server | 8 |
| AP2 v0.2.0 signed mandate | AP2 mandate engine, secp256k1 signing | 9 |
| Seller Authorization Manifest | seller_manifest.py, DNSid-signed manifest | 10 |
| Visa TAP credential | visa_tap.py, RFC 9421 Ed25519 headers | 14 |
| Mastercard Verifiable Intent | mastercard_agent_pay.py, Intent Artifact | 14 |

The identity layer is not theoretical. SupplyMind has built each component
individually. The proposal asks Firmly and LoginID to integrate them into a
unified product layer on top of their existing infrastructure.
