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

**1. Identity** — who is the agent, who does it represent, and who vouches for it?

**2. Scoping** — what is the agent allowed to do, and how is it constrained?

**3. Approvals** — who approves what the agent is about to do, and how?

**4. Enforcement** — how do we ensure the agent does only what was approved,
in real time?

Clerk also identifies three keys to agent proliferation: task specification,
approval mechanism, and enforcement engine. Current approaches for each include
AgentPass (Clerk), Mission-bound OAuth (Karl McGuinness), AAuth (Dick Hardt),
MCP Auth (Linux Foundation), and XAA + ID-JAG (Okta).

**How SupplyMind answers each question across all 15 phases:**

| Question | SupplyMind Answer | Phases | Status |
|----------|------------------|--------|--------|
| Identity | secp256k1 + KYA + DID + DNSid | 7, 8 | Partial (Phase 8 planned) |
| Scoping | AP2 Mandate constraints + ACF tiers | 4, 9 | Partial (Phase 9 planned) |
| Approvals | Signed Intent Mandate | 9 | Planned |
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
**Maturity:** Production stable. LF-governed, versioned spec, multi-vendor
implementation, wide enterprise adoption.

**Problem it solves:**
AI agents are powerful reasoners but have no built-in way to access external
tools: databases, APIs, shipping calculators. MCP defines a standard interface
so any agent can call any tool without custom wiring per model.

**How we used it:**
Inventory Server (SQLite-backed, 15 products) and Shipping Server (stub cost
estimator), both built with FastMCP. The Phase 4 Payment Server also exposes
all payment tools over MCP so the buyer agent can create mandates, check ACF
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
- SupplyMind chose MCP because it is now the Linux Foundation standard and the
  only tool interface layer with multi-vendor production adoption.

**Security loopholes:**

- [Identity] No tool-level authorization. MCP defines how to call tools, not
  who is allowed to call them. Any agent that can reach the MCP server can call
  any tool. In production, every MCP server needs an auth layer (API key, OAuth
  token, or mTLS). Without this, a rogue agent can drain inventory data or
  trigger payments.

- [Identity] No caller identity on tool calls. When the inventory server
  receives a get_product call, it cannot verify which agent called it. Audit
  trails are incomplete: you know a tool was called but not who called it.
  Phase 8 wires DNSid so tool calls can carry caller identity.

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
Requires MCP (Phase 1) for the inventory data that populates the catalog.
Without UCP, the buyer agent has no machine-readable way to discover what the
seller offers — it would require custom parsing per seller. Phase 12 (ACP)
extends this by adding a second catalog protocol; without UCP in place first,
Phase 12 has nothing to route from.

**Alternatives considered:**
- ACP (OpenAI + Stripe, Phase 12) is the main competitor at this layer.
  UCP uses JSON-LD and schema.org targeting semantic interoperability across
  any buyer agent; ACP uses a more REST-native format targeting the ChatGPT
  and OpenAI ecosystem specifically. SupplyMind chose UCP first because of the
  Google/Walmart/Shopify coalition weight and B2B catalog semantics.
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
  journey extension and in AP2 Cart Mandates (Phase 9).

**Why this matters:**
UCP solves the Tower of Babel problem for catalog data. But a shared schema
only creates interoperability — it does not create trust. Catalog tells you
what a seller offers; it does not prove the catalog is authentic or current.
UCP + secp256k1 signatures + AP2 Cart Mandates is the complete picture.

---

## Phase 3: A2A — Agent-to-Agent Protocol

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
Requires UCP (Phase 2) for the seller to have something meaningful to advertise
in its Agent Card capabilities. Without A2A, buyer and seller have no standard
discovery or task coordination mechanism — every interaction requires knowing
the seller's URL in advance. Phase 6 (NANDA) extends A2A discovery to the open
web; without A2A Agent Cards, NANDA has no standard format to index.

**Alternatives considered:**
- OpenAI Agents SDK coordination patterns handle multi-agent orchestration
  within the OpenAI ecosystem but are not interoperable with non-OpenAI agents.
- LangGraph provides agent coordination for LangChain-based systems but is a
  framework, not a protocol — no standard wire format for cross-vendor agents.
- Direct REST without discovery is viable for known, fixed seller URLs but
  does not scale to an open marketplace where sellers are unknown in advance.
- SupplyMind chose A2A because it is the only published, LF-governed agent
  coordination protocol with real enterprise adoption.

**Security loopholes:**

- [Identity] Agent Card spoofing. The Agent Card is a JSON document at a
  well-known URL. Any server can serve a card claiming to be any agent. A DNS
  hijack or BGP route leak could redirect the buyer to a fraudulent seller.
  A2A v1.2 adds signed Agent Cards with cryptographic domain verification.
  Phase 8 adds DNSid ownership verification on top.

- [Identity] Task endpoint trust. The buyer sends purchase orders to whatever
  URL the Agent Card specifies. If the card is spoofed, orders go to the
  attacker. There is no challenge-response to confirm the task endpoint is
  controlled by the same entity that signed the card.

- [Scoping] No task integrity. Once a task is submitted, the task contents
  are trusted as-is. There is no mechanism in A2A to verify that the task was
  not modified in transit. AP2 Cart Mandates (Phase 9) solve this by signing
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

## Phase 3: x402 — HTTP 402 Payment Required

**Type:** Protocol
**Established by:** Coinbase (open-sourced May 2025). x402 Foundation launched
April 2 2026, co-founded by Coinbase and Linux Foundation. Coalition includes
Stripe, Cloudflare, AWS, Google, Microsoft, Visa, and Mastercard.
**Adoption:** 119 million transactions on Base, 35 million on Solana as of
March 2026. ~$600M annualized protocol volume, ~$28,000 daily real commerce volume.
**Maturity:** Maturing. LF foundation, major coalition, real transaction volume,
but on-chain verification infrastructure still maturing in tooling.

**Problem it solves:**
Traditional billing is too heavy for micro-transactions. x402 repurposes HTTP's
dormant 402 status code for pay-per-request: server returns 402 with a payment
challenge, client pays, retries with proof, gets the data.

**How we used it:**
Bulk quotes above $500 trigger a 402 response with USDC payment instructions.
Buyer reads the challenge, simulates a USDC payment, retries with a transaction
hash in the X-Payment header. Seller currently accepts any non-empty header.
Phase 16 replaces this with real on-chain verification.

**Dependencies and sequencing:**
Requires A2A (Phase 3) for the buyer to have found the seller and initiated
a task before a payment challenge arises. Phase 8 (DNSid) adds a gate that
must pass before x402 fires. Phase 16 (real settlement) requires a funded
wallet from Phase 13. Skipping x402 means bulk quotes have no access control
— any agent can request them for free.

**Alternatives considered:**
- Stripe metered billing handles per-request API charging but requires a
  Stripe account, monthly invoices, and a human billing relationship — too
  heavy for machine-to-machine micropayments between unknown agents.
- Traditional API keys with rate limiting prevent abuse but do not create
  economic signals — a key either works or it does not, with no per-use cost.
- Lightning Network micropayments achieve similar per-request economics using
  Bitcoin but require Lightning node infrastructure on both sides; x402 on
  Base is simpler to deploy and uses stablecoins (no price volatility).
- SupplyMind chose x402 because of the LF foundation, the Stripe/Visa/Mastercard
  coalition, and native USDC support on Base.

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

- [Identity] DNSid gate missing. The x402 flow currently does not verify the
  counterparty's identity before accepting payment. Phase 8 adds this gate:
  resolve the counterparty's DNSid before the micro-payment fires, and reject
  if revoked.

**Why this matters:**
x402 is the first protocol in this stack that moves real value. Every security
gap in x402 has a direct financial consequence. The current implementation is
appropriate for local development but is not production-safe without on-chain
verification, replay prevention, and DNSid gating.

---

## Phase 4: AP2 — Agent Payments Protocol

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
without a keypair, you cannot sign Intent or Cart Mandates. Phase 8 (DNSid)
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
- SupplyMind chose AP2 because of Google's institutional backing, the 60+
  partner coalition, and explicit B2B procurement use case alignment.

**Security loopholes:**

- [Approvals] Mandate is unsigned. The current mandate is a Python dict in
  memory. There is no cryptographic proof it was set by the authorized human
  and not modified by the agent process. Phase 9 signs mandates with the
  human's secp256k1 key, making tampering detectable.

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

## Phase 4: ACF — Agentic Commerce Framework

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
ACF tiers are implemented inside the AP2 mandate check. Without AP2 (Phase 4),
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
  infrastructure SupplyMind does not currently have. Phase 14 (fraud detection)
  creates the data needed to eventually build dynamic risk scoring.
- SupplyMind chose ACF because tiered autonomy is the simplest model that
  preserves human oversight without requiring human action on every transaction.

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

## Phase 4: MPP — Machine Payments Protocol

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
envelope. The ACF governance layer sits above both rails.

**Dependencies and sequencing:**
Requires AP2 (Phase 4) to have already authorized the payment before MPP
executes it. MPP handles execution; AP2 handles authorization. Skipping MPP
means the agent must know which rail to use for each transaction — it becomes
the agent's problem rather than the payment abstraction layer's problem.

**Alternatives considered:**
- Stripe alone (fiat only) is simpler but excludes the stablecoin settlement
  path needed for x402 micro-payments and Phase 16.
- Circle Programmable Wallets alone (stablecoin only) excludes merchants who
  only accept card payments.
- AWS AgentCore Payments (Phase 16) is a managed implementation of x402 and
  Coinbase/Stripe rails — essentially MPP as a service. SupplyMind builds MPP
  manually first to understand the plumbing; Phase 16 evaluates AgentCore as
  the managed alternative.
- SupplyMind chose MPP to remain rail-agnostic from the start, reflecting the
  likely production reality where different counterparties require different rails.

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

## Phase 6: NANDA — Decentralized Agent Registry

**Type:** Protocol (W3C Verifiable Credential + REST registry)
**Established by:** Project NANDA (projectnanda.org). Open, decentralized.
No single governing organization.
**Adoption:** Early. NANDA NEST is the production registry. Registration
requires HTTPS endpoints; localhost deployments are structurally excluded.
**Maturity:** Experimental. Live registry, but governance model and spec
stability are still forming.

**Problem it solves:**
How does a buyer agent find a seller agent it has never interacted with,
without knowing its URL in advance? NANDA is a decentralized registry where
agents publish their capabilities as W3C Verifiable Credentials. Any agent
can search NANDA and find peers by capability, tag, or DID.

**How we used it:**
AgentFacts document (W3C VC, JSON-LD) generated by src/seller_agent/nanda_facts.py.
Signed with the seller's secp256k1 key. Attempted registration to
nest.projectnanda.org (rejected for localhost, expected behavior). Structure
is production-ready; deployment requires a public HTTPS host.

**Dependencies and sequencing:**
Requires Phase 7 (secp256k1 + KYA) to have run first — the NANDA AgentFacts
document is signed with the same key as the KYA document. Without a signed
identity, NANDA registration is self-asserted with no proof. Phase 8 (DNSid)
adds an ownership verification gate that should run after NANDA discovery
and before any transaction begins.

**Alternatives considered:**
- Maritime.sh is a cloud hosting platform for agents (~$1/month) that provides
  agent discovery as part of its hosting service. It is simpler to set up than
  a self-hosted NANDA registration but introduces a centralized dependency.
- Enterprise service registries (Consul, etcd, API gateways) handle agent
  discovery within a single organization but are not interoperable across
  organizational boundaries — exactly the open marketplace problem SupplyMind
  is trying to solve.
- Centralized directories (a single org maintaining a curated agent list) are
  simpler but create a single point of failure and a governance bottleneck.
- SupplyMind chose NANDA because it is the only open, decentralized,
  W3C-VC-based agent registry available. The HTTPS constraint is a known
  limitation for local development.

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
defense-in-depth: NANDA finds candidates, KYA verifies identity, DNSid verifies
ownership, A2A coordinates the task. No single layer is sufficient alone.

---

## Phase 7: KYA + Cryptographic Identity (secp256k1, DID, KYA)

**Type:** Framework (with W3C DID spec as the underlying protocol)
**Established by:** DID spec by W3C. KYA as a pattern by MIT and industry
(Sumsub, Trulioo) circa 2025. secp256k1 is the same elliptic curve used by
Bitcoin and Ethereum.
**Adoption:** Emerging. DID:web is widely understood; production KYA
implementations are nascent.
**Maturity:** Maturing (secp256k1 + DID — battle-tested cryptography).
Experimental (KYA as an agent identity pattern — nascent implementations).

**Problem it solves:**
In agent commerce, a buyer needs to verify that the seller it is talking to is
who it claims to be — without a centralized authority to ask. KYA uses
cryptographic proof: the seller publishes a document signed with a private key;
the buyer verifies the signature using the public key.

**How we used it:**
secp256k1 keypair generated and persisted in .keys/seller_private_key.hex
(gitignored). DID derived as did:web:localhost:8080. KYA document built and
signed in src/identity/kya_builder.py. NANDA AgentFacts signed with the same
key in src/seller_agent/nanda_facts.py. Buyer can verify any signed document
using verify_signature() from src/identity/keys.py.

**Dependencies and sequencing:**
Phase 7 is the cryptographic foundation for Phases 8, 9, 10, and 13. DNSid
(Phase 8) anchors the key to a DNS domain. Signed Mandates (Phase 9) use the
same signing infrastructure. Visa TAP (Phase 14) adds a network-level credential
on top of the key-based identity. Skipping Phase 7 means every downstream phase
that requires signatures has nothing to sign with.

**Alternatives considered:**
- ENS (Ethereum Name Service) provides human-readable names anchored on
  Ethereum mainnet. More decentralized than did:web but requires on-chain
  transactions to register and update, adding cost and latency.
- did:ion (Microsoft, Bitcoin-anchored) provides stronger decentralization
  guarantees than did:web but requires Bitcoin infrastructure and is slower
  to resolve.
- did:key requires no infrastructure at all (the key is the identifier) but
  provides no revocation mechanism — once a key is compromised, there is no
  way to signal that. This makes it unsuitable for production.
- SupplyMind chose did:web because it requires no blockchain infrastructure,
  is fast to resolve, and is the most widely supported DID method. The
  revocation gap is addressed by DNSid in Phase 8.

**Security loopholes:**

- [Identity] No key revocation. If the private key is compromised, there is
  no way to signal that signatures from that key should no longer be trusted.
  Every signed document from the compromised key remains cryptographically valid
  until all relying parties rotate their trust anchor. DNSid (Phase 8) solves
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

**Why this matters:**
Cryptographic identity is necessary but not sufficient for enterprise trust.
It answers "was this signed by the claimed key?" but not "should I trust this
key?" The answer to the second question requires ownership registries (DNSid),
network-level credentials (Visa TAP, Mastercard Agent Pay), and revocation
infrastructure. Phase 7 lays the foundation; Phases 8 and 13 make it
enterprise-grade.

**The missing layer: business entity verification (KYA gap)**

Phase 7 proves the agent signed its own credential. DNSid (Phase 8) proves
the agent controls a domain. Neither answers the question that every payment
rail, lender, and supplier actually needs: is the business behind this agent
real, solvent, and legally clean?

This is the KYA gap. An agent can have a perfect secp256k1 signature and a
valid DNSid handle and still represent a shell LLC incorporated yesterday at
a vacant lot, sanctioned, or under active litigation. Cryptographic identity
and business entity verification are orthogonal problems. The first proves
the agent is who it claims to be. The second proves the claimed entity is
worth trusting.

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
| Baselayer | Graph AI over SOS, EIN, OFAC, liens, litigation. Immutable Business ID carried by the agent. MCP server integration planned. | $6.5M seed (Torch Capital, Founder Collective, Afore). B2B focus. |
| Skyfire | KYAPay protocol: signed JWTs carrying verified identity claims (who built the agent, who authorized it, what it can do, how it pays). | $9.5M total (a16z CSX, Coinbase Ventures, Neuberger Berman). Partnered with Experian. |
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
the transaction protocol stack (MCP, A2A, UCP, AP2, ACP) and documents where
an external trust oracle would plug in. That gap, between cryptographic identity
and business entity verification, is exactly where a $6.5M seed company is
building today. SupplyMind's architecture is a working prototype of the layer
above theirs.

---

## Phase 8: DNSid — Agent Ownership Registry (Done)

**Type:** Protocol
**Established by:** Identity Digital Innovation Labs (dnsid.ai), launched
April 27 2026. Linux Foundation Decentralized Trust member. Neutral governance.
**Adoption:** Very early. Launch-stage as of May 2026.
**Maturity:** Experimental. Brand new protocol with no production deployments
as of May 2026.

**Problem it solves:**
Cryptographic identity (Phase 7) proves a document was signed by a key. It does
not prove who owns the key or whether the agent using it is still authorized to
act. DNSid is the ownership registry: it anchors an agent's identifier to a DNS
domain, records the owner, and provides revocation. When an agent is compromised
or decommissioned, its DNSid handle is revoked and all downstream systems that
check before transacting will reject it.

This is the layer that transforms SupplyMind from autonomous to accountable.

**Dependencies and sequencing:**
Requires Phase 7 (secp256k1 + KYA) — DNSid anchors the existing cryptographic
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
- SupplyMind chose DNSid because it is vendor-neutral, LF Decentralized Trust
  member, DNS-anchored (reusing existing infrastructure), and specifically
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
with cryptographically signed Intent Mandates (human signs upfront) and Cart
Mandates (agent signs at purchase time, linked back to Intent Mandate). Creates
a tamper-proof audit trail from human intent to payment execution.

**Dependencies and sequencing:**
Requires Phase 7 (secp256k1) for the signing infrastructure. Requires Phase 8
(DNSid) for the vendor_dnsid field in Cart Mandates and for the DNSid gate that
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

**Type:** Novel spec (no existing standard -- borrows AP2 v0.2.0 cryptographic pattern)
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
goes live. It states what the agent may sell, at what price ranges, with what
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
cryptographic pattern (secp256k1-signed document, human operator key, agent
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
mobile confirm for mid-market), Approach 3 (ERP/PIM MCP integration, LoginID
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

**Type:** Application (implements DNSid, AP2, x402, NANDA as data sources)
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
A buyer agent built on GPT-4o speaks ACP, not UCP. SupplyMind sellers currently
only speak UCP. Adding ACP makes the seller reachable from any commerce AI
regardless of which LLM powers the buyer. Merchants supporting both see ~40%
more agentic traffic than single-protocol merchants.

**Dependencies and sequencing:**
Requires UCP (Phase 2) to already exist — the protocol router needs a UCP
handler to route from before an ACP handler can be added alongside it.
The AP2 mandate engine (Phase 4) sits above both protocols and enforces the
same spending policy regardless of which checkout protocol the buyer used.

**Alternatives considered:**
- UCP only: simpler, but partitions the seller from all non-Gemini buyer agents.
  Single-protocol lock-in in a two-protocol world costs approximately 40%
  of accessible agentic traffic based on current data.
- ACP only: stronger B2C traction but weaker B2B semantic catalog support.
  UCP's JSON-LD and schema.org vocabulary is better suited to SupplyMind's
  B2B procurement use case.
- SupplyMind chose both via a protocol router because the cost of a router is
  low and the cost of protocol lock-in is high in a still-settling ecosystem.

**Security loopholes:**

- [Identity] Protocol router must not bypass DNSid gates. A buyer coming in
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

## Phase 13: Agent Wallet Layer (13a Done -- mock; 13b optional with real APIs)

**Type:** Implementation (Stripe Link Agent Wallet + Coinbase/Base MCP)
**Maturity:** Maturing. Stripe Link and Coinbase wallets are production-grade;
Base MCP (launched May 26 2026) is early.

**Problem it solves:**
The current payment rails are simulated. Phase 12 introduces real wallet
infrastructure: Stripe Link for fiat (one-time virtual card per agent task)
and Coinbase Agentic Wallet for stablecoin (USDC, programmable spending
policies, non-custodial identity anchored to DNSid).

**Dependencies and sequencing:**
Requires AP2 mandates (Phase 4/9) to be in place before real money flows —
a funded wallet without a spending policy is a liability. Phase 16 (x402 real
settlement) requires the Coinbase/Base wallet from Phase 13. Skipping Phase 13
means Phase 16 has no funded wallet to draw from.

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

## Phase 14: Network Credential Layer — Visa TAP + Mastercard Agent Pay (Planned)

**Type:** Protocol (Visa TAP) + Framework (Mastercard Agent Pay)
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
Requires Phase 8 (DNSid) — Visa TAP and Mastercard Agentic Tokens are bound
to a specific agent identity; DNSid provides the ownership layer that makes
that binding meaningful. Requires Phase 13 (real wallets) — network credentials
are meaningless without a real payment instrument behind them.

**Alternatives considered:**
- Visa TAP and Mastercard Agent Pay are not mutually exclusive. Full network
  coverage requires both, since issuer acceptance depends on which network
  the cardholder's account runs on.
- Relying on AP2 Mandates alone (no network credential) is viable for
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

**Why this matters:**
Financial institution deployment requires network-level credentials. A bank
cannot accept autonomous payments from an agent identified only by a self-issued
DID and a local mandate. Visa TAP and Mastercard Agent Pay are the credentials
that existing financial infrastructure recognizes.

---

## Phase 15: Fraud and Bot Detection (Planned)

**Type:** Implementation (Stripe Radar + DNSid rate limiting)
**Maturity:** Experimental (DNSid-anchored rate limiting is novel).
Maturing (Stripe Radar is production-grade).

**Problem it solves:**
MCP traffic increased 50x in one week after Anthropic connector expansion.
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
buyer's Coinbase wallet. Requires Phase 8 (DNSid gates on x402 path) — real
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
  x402 USDC; small procurement goes AP2 + Stripe Link; large procurement
  goes AP2 + Visa TAP/MC Agent Pay. The decision is by transaction size, not
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
| 1 | MCP | Protocol | Anthropic / LF | Agent-to-tool | Production stable | Done |
| 2 | UCP | Protocol | Google + coalition | Catalog + checkout | Maturing | Done |
| 3 | A2A | Protocol | Google DeepMind / LF | Agent discovery + tasks | Maturing | Done |
| 3 | x402 | Protocol | Coinbase / LF | Micro-payment | Maturing | Simulated |
| 4 | AP2 v0.1 | Protocol | Google | Payment governance | Maturing | Done |
| 4 | ACF | Framework | Vincent Dorange | Tiered autonomy | Experimental | Done |
| 4 | MPP | Protocol | Stripe + Tempo | Multi-rail settlement | Experimental | Simulated |
| 5 | (partial) | | | Protocol reflection, 2nd seller | | Partial |
| 6 | NANDA | Protocol | Project NANDA | Decentralized registry | Experimental | Done (localhost) |
| 7 | KYA + secp256k1 | Framework + Protocol | W3C + industry | Cryptographic identity | Maturing / Experimental | Done |
| 8 | DNSid | Protocol | Identity Digital | Ownership + revocation | Experimental | Planned |
| 9 | AP2 v0.2.0 | Protocol | Google | Signed mandates | Experimental | Planned |
| 10 | Governance Dashboard | Application | SupplyMind | Audit + oversight | N/A | Planned |
| 11 | ACP | Protocol | OpenAI + Stripe | Multi-protocol checkout | Maturing | Planned |
| 12 | Stripe Link + Coinbase | Implementation | Stripe, Coinbase | Agent wallet layer | Maturing | Planned |
| 13 | Visa TAP + MC Agent Pay | Protocol + Framework | Visa, Mastercard | Network credentials | Maturing | Planned |
| 14 | Stripe Radar + DNSid | Implementation | Stripe + SupplyMind | Fraud detection | Experimental | Planned |
| 15 | x402 (LF) + AWS AgentCore | Protocol + Managed infra | LF + AWS | Real settlement | Experimental | Planned |

---

## What SupplyMind Leaves Open

After all 15 phases are complete, four questions from Clerk's agentic auth
analysis are answered to varying degrees. This section is an honest accounting
of what remains unresolved.

### Identity: largely answered

After Phase 8, SupplyMind can answer who an agent is (secp256k1 + KYA), who
owns it (DNSid), and whether its owner vouches for it (DNSid registry). What
remains open: identity is not enforced at the MCP tool call level. Individual
tool calls carry no signed caller identity. An agent with a valid DNSid can
call any MCP tool on a server it can reach. Closing this gap requires per-call
auth at the MCP transport layer — something MCP Auth (Linux Foundation) and
AgentPass (Clerk) are working toward but SupplyMind does not implement.

### Scoping: partially answered

After Phase 9, SupplyMind can constrain what an agent spends (AP2 mandate),
against which vendors (approved list + DNSid gate), and within what ACF tier
thresholds. What remains open: scoping is defined by amount and vendor, not
by task. An agent operating within its spending mandate can still purchase
categories of goods not intended by the human. Mission-bound OAuth and
task-scoped credentials (Clerk AgentPass) would close this gap by binding the
agent's authorization to a specific task description, not just a spending bound.

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
