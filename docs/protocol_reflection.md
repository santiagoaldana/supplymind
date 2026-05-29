# SupplyMind Protocol Reflection

**Author:** Santiago Aldana
**Project:** SupplyMind, a hands-on multi-agent B2B commerce prototype
**Date:** May 2026

This document reflects on each protocol and framework used in SupplyMind: what problem it solves, whether it is a protocol or a framework, who established it, how widely it is adopted, and what surprised me building with it.

---

## Protocols vs. Frameworks

A **protocol** is a precise, machine-enforceable specification. Both sides must implement it exactly or communication fails. It defines what messages look like and what must happen at the wire level.

A **framework** is a set of principles, recommended practices, and architectural patterns. It guides how you think about and structure a problem but allows implementation flexibility. Deviating from a framework does not break the system; it just means you are doing it differently.

Some entries below sit in between: they have a formal spec (protocol-like) but also governance guidance (framework-like). The classification reflects the dominant intent.

---

## MCP: Model Context Protocol

**Type:** Protocol

**Established by:** Anthropic. Announced November 2024. Donated to the Linux Foundation's Agentic AI Foundation in December 2025, now governed as an open standard under Apache 2.0 with founding members including OpenAI, Google, Microsoft, AWS, and Block.

**Adoption:** Dominant. By April 2026, over 9,400 MCP servers are publicly registered, up from 1,200 in early 2025. 78% of enterprise AI teams report at least one MCP-backed agent in production. All major AI platforms (OpenAI, Google, AWS, Microsoft, Cursor, VS Code) have native MCP support. It is the closest thing the industry has to a universal agent-to-tool standard.

**Problem it solves:**
AI agents are powerful reasoners but have no built-in way to access external tools: databases, APIs, shipping calculators. MCP defines a standard interface so any agent can call any tool without custom wiring.

**How we used it:**
We built two MCP servers from scratch using FastMCP: an Inventory Server (SQLite-backed, 15 products) and a Shipping Server (stub cost estimator). The Phase 4 Payment Server also exposes all payment tools over MCP so the buyer agent can create mandates, check ACF decisions, and execute payments as standard tool calls.

**What surprised me:**
MCP is not an AI feature. It is plumbing. The agent does not know or care that the tool is MCP. What MCP provides is a standard contract so the same tool can be called by Claude, Gemini, or any future agent without rewriting the tool. This is the B2B middleware insight: standardize the interface, not the implementation.

**LinkedIn-ready quote:**
"I built MCP servers from scratch and realized the protocol is not about AI. It is about making tools agent-agnostic so any model can use them without custom integration."

---

## A2A: Agent-to-Agent Protocol

**Type:** Protocol

**Established by:** Google DeepMind. Announced April 2025 with 50 founding partners. Contributed to the Linux Foundation's Agentic AI Foundation in June 2025. Now at version 1.2, governed under Apache 2.0. Version 1.2 adds signed Agent Cards with cryptographic domain verification.

**Adoption:** Strong enterprise adoption. Over 150 organizations in production as of April 2026, including Microsoft, AWS, Salesforce, SAP, ServiceNow, Workday, and IBM. Azure AI Foundry, Amazon Bedrock AgentCore, and Google Cloud all provide native A2A integration. It started with 50 partners in April 2025 and tripled to 150+ production deployments in one year.

**Problem it solves:**
When two AI agents need to collaborate, one buying and one selling, how do they find each other and coordinate work? A2A defines a discovery mechanism (Agent Cards) and a task lifecycle (submit, poll, complete) so agents can transact without human coordination at each step.

**How we used it:**
The Seller Agent publishes an Agent Card at `/.well-known/agent-card.json` listing its capabilities and task endpoint. The Buyer Agent fetches this card as its first action, then sends purchase orders to `POST /tasks/send` and polls `GET /tasks/{id}` for confirmation.

**What surprised me:**
The Agent Card is conceptually identical to a business card or a REST API's OpenAPI spec. It is a capability declaration. The insight is that discovery is the hardest part of agent-to-agent commerce. Once discovery is standardized, the rest is just HTTP.

**LinkedIn-ready quote:**
"A2A taught me that the hardest part of multi-agent commerce is not AI. It is discovery. Once agents can find and describe each other, the transaction is just HTTP."

---

## UCP: Universal Commerce Protocol

**Type:** Protocol

**Established by:** Google, co-developed with Shopify, Walmart, Target, Etsy, Wayfair, BigCommerce, PayPal, and Stripe. Announced by Sundar Pichai at NRF 2026 (January 11, 2026). Version 2026-04-08 released April 8, 2026 under Apache 2.0.

**Adoption:** Early but high-signal. The founding coalition of 20+ retailers and payment networks covers a significant share of US e-commerce GMV. The spec extends beyond catalog discovery to the full checkout journey: browse, cart, checkout, and order status. Widespread merchant-level implementation is still in progress as of mid-2026.

**Problem it solves:**
Product catalogs are a Tower of Babel: every seller uses different field names, formats, and schemas. UCP defines a machine-readable catalog format using JSON-LD and schema.org so any buyer agent can parse any seller's catalog without custom code.

**How we used it:**
We built our own Phase 2 UCP implementation serving a JSON-LD product catalog at `/.well-known/ucp.json`. The Buyer Agent fetches this and selects products using pure rule-based logic, no LLM needed, because the schema is predictable. Phase 5C upgrades this to the official UCP v2026-04-08 spec, which extends the protocol to cover the entire checkout journey.

**What surprised me:**
The value of schema.org is not the vocabulary. It is the contract. When every field has a globally agreed-upon definition, you can parse a catalog from a seller you have never met before. This is what interoperability actually means.

**LinkedIn-ready quote:**
"Building UCP showed me that interoperability is not a technical problem. It is a contracts problem. When every field has a shared definition, agents can trade with strangers."

---

## KYA: Know Your Agent

**Type:** Framework (with emerging protocol-like implementations via W3C DIDs)

**Established by:** No single author. The term crystallized in early 2025 through concurrent academic research from MIT and enterprise initiatives from identity verification firms including Sumsub and Trulioo. It is an industry-wide concept rather than a specification from one organization. Formal implementations converge around W3C Decentralized Identifier standards.

**Adoption:** Emerging and mostly conceptual. KYA is widely discussed as the next essential trust layer for agentic commerce but formal, interoperable implementations are nascent. Most current deployments are proprietary or proof-of-concept. Analyst projections place mainstream adoption in the 2027 to 2028 timeframe as regulatory pressure on AI agent identity increases.

**Problem it solves:**
In human commerce, identity verification (KYC) prevents fraud. In agent commerce, a buyer agent needs to verify that the seller it is talking to is who it claims to be. KYA defines a machine-readable identity document using DIDs (Decentralized Identifiers) so agents can verify each other without a centralized registry.

**How we used it:**
The Seller publishes a KYA document at `/.well-known/kya.json` containing its DID, name, jurisdiction, and a cryptographic proof placeholder. The Buyer reads this as part of discovery to confirm seller identity before placing an order.

**What surprised me:**
DIDs are not blockchain-native. A `did:web` identifier is just a domain plus a path with a JSON document. The decentralization comes from the cryptographic proof, not the storage. In Phase 5 we use a proof placeholder. Production would use a real secp256k1 signature.

**LinkedIn-ready quote:**
"KYA made me realize that AI agent identity is an unsolved problem hiding in plain sight. Every agentic commerce system needs it, but almost none have it yet."

---

## x402: HTTP 402 Payment Required

**Type:** Protocol

**Established by:** Coinbase. Open-sourced in May 2025 via the GitHub repo `coinbase/x402`. The x402 Foundation, co-founded by Coinbase and the Linux Foundation, launched April 2, 2026, with Stripe, Cloudflare, AWS, Google, Microsoft, Visa, and Mastercard as founding coalition members.

**Adoption:** High institutional signal, early real-world volume. As of March 2026, x402 has processed over 119 million transactions on Base and 35 million on Solana, with roughly $600M in annualized volume at the protocol level. Real commerce volume remains small (approximately $28,000 in daily volume), with much current activity from testing. The coalition membership is the stronger signal of future trajectory.

**Problem it solves:**
Some API data is valuable enough to charge for, but traditional billing (monthly invoices, SaaS subscriptions) is too heavy for micro-transactions. x402 repurposes HTTP's dormant 402 status code to create a pay-per-request protocol: the server returns 402 with a payment challenge, the client pays, retries with proof, and gets the data.

**How we used it:**
Bulk quotes above $500 trigger a 402 response with USDC payment instructions. The Buyer Agent reads the challenge, simulates a USDC payment, and retries with a transaction hash in the `X-Payment` header. The Seller accepts any non-empty header in Phase 3. Phase 4 would verify on-chain.

**What surprised me:**
HTTP 402 was defined in 1996 and reserved for "Payment Required," then never used for 30 years because micropayments had no viable infrastructure. Stablecoins on fast, cheap blockchains are the missing piece. x402 is what HTTP always intended.

**LinkedIn-ready quote:**
"x402 is a 1996 HTTP status code that finally makes sense in 2026. Stablecoins gave HTTP its missing payment primitive."

---

## AP2: Agent Payments Protocol

**Type:** Protocol

**Established by:** Google. Announced September 16, 2025 with over 60 founding partners including PayPal, Mastercard, American Express, Adyen, Coinbase, Salesforce, ServiceNow, Worldpay, JCB, UnionPay International, and Etsy. Released as open source under Apache 2.0.

**Adoption:** Broad institutional backing from day one. With Mastercard, Adyen, PayPal, and American Express as launch partners, AP2 has more payment network coverage than any other agentic payment protocol at launch. Enterprise platform integrations are underway but widespread merchant-level adoption is still maturing. AP2 is distinct from x402 and MPP in that it explicitly prioritizes agent intent verification: ensuring the agent is purchasing the way the human intends, not just that the payment clears.

**Problem it solves:**
An AI agent with unrestricted payment authority is a liability. AP2 defines spending Mandates: structured contracts that the human operator sets once and the agent enforces on every payment. The agent can only pay approved sellers, up to defined limits, under defined conditions.

**How we used it:**
Before every procurement run, a Mandate is created: approved sellers, per-transaction limit, total spend limit. Every payment attempt calls `check_mandate()` first. The agent cannot bypass this check. It is enforced in the payment server, not in the agent's logic.

**What surprised me:**
The Mandate is not a feature for the agent. It is a feature for the human. The insight is that agentic commerce governance is not about making agents smarter; it is about giving humans durable, auditable control even when they are not watching.

**LinkedIn-ready quote:**
"AP2 taught me that the key design question for agentic payments is not how to make the agent autonomous. It is how to make the human's policy durable."

---

## ACF: Agentic Commerce Framework

**Type:** Framework

**Established by:** Vincent Dorange, 2025. Governed independently at acfstandard.com. Not affiliated with a major technology company or standards foundation. Structured around four principles: Decision Sovereignty, Governance by Design, Ultimate Human Control, and Traceable Accountability.

**Adoption:** Niche but influential in governance discussions, particularly in Europe where regulatory pressure on AI autonomy is strongest. ACF is not a wire-level protocol that systems implement; it is a governance model that organizations adopt at the policy level, making adoption harder to measure than protocol adoption. It is referenced in enterprise AI governance conversations more than in developer implementation contexts.

**Problem it solves:**
Binary human approval (approve everything or approve nothing) does not scale with agentic commerce. ACF defines tiered autonomy: small payments execute automatically, medium payments execute with a notification, large payments require explicit human approval.

**How we used it:**
Three tiers based on amount: AUTO (under $5) executes immediately with no notification; NOTIFY ($5 to $10) executes and logs a human notification; BLOCK (over $10) stops and prompts the human at the terminal.

**What surprised me:**
The tiers are arbitrary. The human sets them. The architectural insight is that the thresholds encode the human's risk tolerance, not the agent's intelligence. A more trusted agent gets wider AUTO bands. This is how you scale human oversight without scaling human labor.

**LinkedIn-ready quote:**
"ACF's tiered autonomy flipped my mental model: the goal is not to make the agent trustworthy. It is to make the human's trust calibration explicit and adjustable."

---

## MPP: Machine Payments Protocol

**Type:** Protocol

**Established by:** Stripe and Tempo, a payments-focused Layer 1 blockchain incubated by Stripe and Paradigm. Released March 18, 2026, the same day Tempo's mainnet went live. Extended with streaming payment primitives at Stripe Sessions 2026 (April 29 to 30, 2026). Open standard, extendable by third parties. Visa (cards), Lightspark (Bitcoin Lightning), Affirm, and Klarna have already published extensions.

**Adoption:** Early but high-credibility. Given Stripe's position as the dominant developer payments platform, MPP has immediate reach into the developer ecosystem. MPP is rail-agnostic: it wraps stablecoins, cards, and Lightning under a single lifecycle-aware envelope, including a streaming micropayments primitive that lets services bill against token-level AI usage in real time rather than lump-sum invoices.

**Problem it solves:**
Different sellers accept different payment methods. One accepts credit cards (fiat), another accepts USDC (stablecoin). A buyer agent should not need to know or care which rail to use. MPP provides a payment abstraction layer where the agent declares intent and the rails figure out execution.

**How we used it:**
Every payment execution runs two rails simultaneously: a fiat rail (Stripe PaymentIntent in test mode) and a USDC rail (simulated Circle USDC transfer). Both return a uniform result envelope. The ACF governance layer sits above both rails and does not care which rail executes.

**What surprised me:**
Building dual rails made me understand why Stripe is building their Agentic Commerce Suite and why Circle matters. The future is not fiat vs. crypto. It is a payment abstraction layer where the agent declares the amount and the rails figure out the rest.

**LinkedIn-ready quote:**
"Building dual-rail settlement showed me that the real infrastructure gap in agentic commerce is not payments. It is payment abstraction. The agent should declare intent, not choose rails."

---

## Competing and Complementary Protocols from the Payments Industry

The protocols above are what SupplyMind was built on. The entries below are from major payments and infrastructure players who are building parallel or overlapping standards. Some compete directly; others are complementary layers.

---

## ACP: Agentic Commerce Protocol (OpenAI + Stripe)

**Type:** Protocol

**Established by:** OpenAI and Stripe, co-developed September 2025. Open source under Apache 2.0, maintained at github.com/agentic-commerce-protocol. Multiple spec versions shipped through April 2026, adding payment handlers, scoped tokens, discount extensions, native MCP transport, and cart/feed/order primitives.

**Adoption:** Significant early traction in B2C retail. As of early 2026, ACP is processing live transactions for Etsy and expanding to over 1 million Shopify merchants, Walmart, and dozens of other retailers. During Cyber Week 2025, retailers with ACP-integrated AI agent discovery saw roughly 7x better sales growth than those without. PayPal adopted ACP in October 2025 to power in-chat payments within ChatGPT. OpenAI charges merchants a 4% fee on completed Instant Checkout purchases. Note: OpenAI shut down its own Instant Checkout initiative in March 2026, shifting toward merchant-controlled checkout, but ACP itself continues as the open standard.

**Problem it solves:**
How does an AI agent inside ChatGPT or another consumer AI surface discover a merchant's catalog, build a cart, and complete a purchase without custom integration for each seller? ACP defines the connective layer between AI agents and businesses: catalog ingestion, cart management, checkout delegation, and authentication, all composable and expressible as either REST endpoints or an MCP server.

**Relationship to SupplyMind protocols:**
ACP is the closest competitor to UCP for the catalog and checkout layer, and overlaps with AP2 on payment delegation. Where UCP focuses on B2B machine-readable catalogs (schema.org/JSON-LD), ACP targets B2C consumer agent checkout. Where AP2 governs mandate enforcement, ACP handles the checkout flow itself. They can coexist: ACP for discovery and cart, AP2 for payment governance.

---

## TAP: Trusted Agent Protocol (Visa)

**Type:** Protocol (with framework characteristics in its governance guidance)

**Established by:** Visa. Announced October 14, 2025 with launch partners including Adyen, Stripe, Worldpay, CyberSource, Elavon, Nuvei, Cloudflare, Microsoft, and Shopify. Specification published openly at github.com/visa/trusted-agent-protocol under a permissive license. Technical standard follows RFC 9421 (HTTP Message Signatures).

**Adoption:** Concentrated on the processor side first, since a single processor integration covers all of its merchant base. Adyen, Stripe, and Worldpay implemented TAP at launch, giving it immediate reach across their combined merchant footprint. Direct merchant integrations are slower due to backend changes required. Visa predicts millions of consumers using AI agents to complete purchases by the 2026 holiday season, with TAP as the trust backbone.

**Problem it solves:**
How does a merchant distinguish a legitimate AI agent acting on behalf of a consumer from a malicious bot scraping or abusing the checkout? TAP adds a digital proof-of-identity to every agent-initiated transaction using cryptographically signed HTTP headers: `Signature-Agent` (agent operator's public key directory), `Signature-Input` (key ID, validity window, tag), and `Signature` (Ed25519 signature over the canonical request). Merchants validate the signature using Visa's public keys. Timestamps and nonces prevent replay attacks.

**Relationship to SupplyMind protocols:**
TAP addresses the same trust gap as KYA but approaches it from the network side rather than the agent side. KYA is about the seller proving its identity to the buyer; TAP is about the buyer's agent proving its legitimacy to the seller and merchant processor. They are complementary identity layers operating in opposite directions.

---

## Agent Pay + Verifiable Intent (Mastercard)

**Type:** Agent Pay is a framework; Verifiable Intent is an open protocol standard

**Established by:** Mastercard. Agent Pay announced April 29, 2025. Verifiable Intent introduced March 5, 2026, built in collaboration with Google, Fiserv, IBM, Checkout.com, Basis Theory, and Getnet. Both are open-sourced on GitHub. Agent Pay entered broad availability across US Mastercard cardholders by November 2025.

**Adoption:** Agent Pay has the broadest consumer card coverage of any agentic payment framework, given Mastercard's global network. Verifiable Intent is early but has protocol-agnostic design (aligned with both AP2 and UCP) and backing from Google, giving it cross-ecosystem reach. Citi and US Bank entered the pilot in September 2025; full US rollout completed November 2025.

**Problem it solves:**
Two distinct problems:

Agent Pay addresses credential security: how does an AI agent transact using a consumer's card without ever holding the raw card number? It uses Agentic Tokens, an extension of Mastercard's Digital Enablement Service (MDES), that bind a tokenized card credential to a specific agent, a specific merchant scope, and a specific consent policy. The token cannot be used outside its defined scope.

Verifiable Intent addresses audit and dispute resolution: when an AI agent completes a purchase, how do all parties (consumer, agent operator, merchant, card network) agree on what was authorized? It creates a tamper-resistant, cryptographically signed record linking the consumer's identity, their specific instructions, and the transaction outcome. Uses Selective Disclosure so each party sees only the minimum information needed to verify authorization or resolve a dispute.

**Relationship to SupplyMind protocols:**
Agent Pay's Agentic Tokens are the network-layer equivalent of AP2 Mandates: both constrain what an agent can pay and to whom. Verifiable Intent is a missing layer in SupplyMind's current design: we have mandate enforcement and ACF tiers, but no tamper-resistant audit record of the human's original intent. In a production system, Verifiable Intent would sit between the human's consent and the AP2 mandate.

---

## AgentCore Payments (AWS)

**Type:** Managed infrastructure layer (not a protocol; implements x402 and Coinbase/Stripe rails)

**Established by:** AWS, in partnership with Coinbase and Stripe. Launched in preview May 7, 2026. Available in US East (N. Virginia), US West (Oregon), Europe (Frankfurt), and Asia Pacific (Sydney).

**Adoption:** Preview stage as of May 2026. Given AWS's position as the dominant cloud platform for enterprise AI workloads, adoption is expected to accelerate rapidly once generally available.

**Problem it solves:**
Building payment capabilities into an agent requires wallet management, policy-based spending controls, on-chain verification, and audit trails; all implemented correctly and securely. AgentCore Payments is a managed service that handles the full payment lifecycle for agents deployed on Amazon Bedrock: wallet authentication, x402 micropayment execution on Base, spending governance, and observability. Developers get agentic payments without building the infrastructure from scratch.

**Relationship to SupplyMind protocols:**
AgentCore Payments is not a protocol; it is a managed implementation of x402 and the Coinbase/Stripe payment rails. It does for payments what Amazon Bedrock AgentCore does for agent hosting: abstracts the plumbing so developers focus on agent logic. SupplyMind built this plumbing manually; AgentCore Payments is what a production version would use in the AWS ecosystem.

---

## Summary

| Name | Type | Established by | Layer | Adoption level |
|---|---|---|---|---|
| MCP | Protocol | Anthropic (now Linux Foundation) | Agent-to-tool | Dominant, 9,400+ servers, 78% enterprise |
| A2A | Protocol | Google DeepMind (now Linux Foundation) | Agent discovery + tasks | 150+ orgs in production |
| UCP | Protocol | Google + Shopify + Walmart coalition | Catalog + checkout | Early, high-signal coalition |
| KYA | Framework | MIT + industry (no single owner) | Agent identity | Emerging, mostly conceptual |
| x402 | Protocol | Coinbase (now Linux Foundation) | Pay-per-request | Early volume, major coalition |
| AP2 | Protocol | Google | Payment governance | 60+ launch partners, maturing |
| ACF | Framework | Vincent Dorange (acfstandard.com) | Tiered autonomy | Niche, influential in EU |
| MPP | Protocol | Stripe + Tempo | Multi-rail settlement | Early, high-credibility |
| ACP | Protocol | OpenAI + Stripe | B2C checkout | Live at Etsy, Shopify; 7x retail uplift |
| TAP | Protocol | Visa | Agent identity (buyer side) | Processor-side live, merchant rollout ongoing |
| Agent Pay | Framework | Mastercard | Card credential governance | Full US coverage, Nov 2025 |
| Verifiable Intent | Protocol | Mastercard + Google | Consent audit trail | Early, protocol-agnostic design |
| AgentCore Payments | Managed infra | AWS + Coinbase + Stripe | Payment execution | Preview, May 2026 |

**The competitive landscape in one sentence:** MCP won the agent-to-tool layer; A2A and ACP are competing for agent-to-agent and agent-to-merchant coordination; Visa (TAP), Mastercard (Agent Pay + Verifiable Intent), and Google (AP2) are each trying to own the trust and payment governance layer; and AWS is commoditizing the payment execution infrastructure so developers do not have to build it themselves.
