# Session Context Export — June 11, 2026

## Who You Are

Santiago Aldana — MIT Sloan MBA, 20+ years FinTech/AI/payments/LATAM leadership.
- Advisor to both **Firmly** and **LoginID**
- Building **SupplyMind** — a hands-on multi-agent B2B agentic commerce system (15+ phases)
- Currently on Phase 14 (Visa TAP + Mastercard Agent Pay)

---

## The News That Started This Session

**June 10, 2026:** Visa announced a partnership with OpenAI at the Visa Payments Forum in San Francisco.
AI agents inside OpenAI products (ChatGPT, Codex) can now initiate Visa transactions at 175M+ merchant locations.

Key official link: https://investor.visa.com/news/news-details/2026/Visa-Partners-with-OpenAI-to-Power-the-Next-Generation-of-AI-Commerce/default.aspx

What Visa brings: tokenized credentials, real-time fraud monitoring, spending caps, merchant category restrictions.
What is new vs. what was already known: TAP itself launched October 2025 (already in SupplyMind Phase 14 plan). What is new is the OpenAI distribution at scale, and Visa ICC going live.

---

## Visa Intelligent Commerce Connect (ICC)

Announced: April 8, 2026
Official link: https://investor.visa.com/news/news-details/2026/Visa-Opens-the-Door-to-AI-Driven-Shopping-for-Businesses-Worldwide/default.aspx

What it is: A single merchant endpoint that routes between TAP, MPP, ACP, and UCP simultaneously. Merchants connect once; ICC handles protocol translation. Claims to be network-agnostic (not just Visa credentials).

Current status: Pilot with Aldar, AWS, Diddo, Highnote, Mesh, Payabli, Sumvin.

What it solves: Eliminates the need for merchants to implement each agentic commerce protocol separately.
What it does NOT touch: Agent-to-agent discovery (A2A, NANDA), spending authorization (AP2 mandates), cryptographic identity (TAP signatures, secp256k1, DIDs), money settlement (USDC, Stripe fiat).

Competitive tension: ICC and Firmly Connect are direct competitors for the same merchant relationship.

---

## Visa Trusted Agent Protocol (TAP)

Announced: October 2025 with 12 launch partners (Adyen, Stripe, Shopify, Cloudflare, Coinbase, Microsoft, Fiserv, Worldpay, CyberSource, Ant International, Checkout.com, Elavon, Nuvei).

GitHub: https://github.com/visa/trusted-agent-protocol

What it is: Identity layer only — not a payment rail. Answers: "is this agent who it claims to be?"

Technical mechanism:
- RFC 9421 HTTP Message Signatures
- Ed25519 cryptography (recommended) or RSA-PSS-SHA256
- Two HTTP headers added to every agent request:
  - Signature-Input: covers @authority, @path, created, expires, nonce, keyId, tag
  - Signature: base64-encoded Ed25519 signature
- Tags: agent-browser-auth (browsing), agent-payer-auth (checkout)
- Verification: CDN proxy (Cloudflare) validates against Visa Agent Registry (public key directory)
- Raw card number never reaches the agent — only a Visa network token

Shared infrastructure: TAP uses the same Cloudflare Web Bot Auth / RFC 9421 foundation as Mastercard Agent Pay.

---

## Mastercard Agent Pay

Announced: April 2025. Agent Pay for Machines (AP4M) launched June 10, 2026.

Key components:
- **Agentic Tokens**: MDES extension. Binds a tokenized card credential to a specific agent, merchant scope, and consent policy. Raw card never reaches agent or merchant.
- **Verifiable Intent**: A signed Intent Artifact stored on Mastercard infrastructure. Captures user's original instruction. Every subsequent transaction references the artifact. Scope violation detection happens at the Mastercard network layer — not at the agent or merchant.
- Spend caps, merchant restrictions, expiration windows enforced at the network layer.
- Aligned with Google AP2 and UCP. AP2 Mandates treated as valid Verifiable Intent.

AP4M (June 2026): 30+ partners including Coinbase, Stripe, Adyen. Credentials recorded on Polygon, Solana, and Base blockchains.

---

## Full 2026 Agentic Payments Stack

These protocols are not competitors — they occupy different layers:

```
COMMERCE LAYER      ACP (OpenAI+Stripe)    — checkout flow between agent and merchant
                    UCP (Google)            — machine-readable product catalogs

IDENTITY LAYER      Visa TAP               — is this agent legitimate? (RFC 9421)
                    Mastercard Agent Pay    — is this agent authorized? (Agentic Tokens)
                    AP2 (Google)            — spending mandate + tiered autonomy

PAYMENT LAYER       MPP (Stripe+Tempo)     — fiat/crypto multi-rail HTTP 402
                    x402 (Coinbase/LF)     — USDC on Base/Solana/Stellar HTTP 402
                    L402 (Lightning)        — Bitcoin Lightning micro-payments

SETTLEMENT          Stripe fiat
                    USDC/Base
                    Bitcoin Lightning
```

Protocol matrix (from Custena landscape report):

| Protocol | Layer | Maturity | Controller |
|---|---|---|---|
| x402 | Payment (HTTP 402) | Live V2 Dec 2025 | Linux Foundation (Coinbase lead) |
| MPP | Payment (HTTP 402) | Live March 2026 | Stripe + Tempo Labs |
| AP2 | Identity + Authorization | V0.1 60+ orgs | Google (primary) |
| Visa TAP | Identity | Developer preview | Visa |
| Visa ICC | Multi-protocol bridge | Live April 8 2026 | Visa |
| Mastercard Agent Pay | Identity + Authorization | Live 9 APAC + LATAM markets | Mastercard |
| ACP | Commerce layer | Spec live | OpenAI + Stripe |

Shared governance: x402 Foundation (Linux Foundation) includes Visa, Mastercard, Stripe, Google, AWS, Cloudflare, Coinbase.

---

## Firmly

Company in Santiago's job search pipeline and advisory network.
Career page: https://firmly.com/careers
Lamp score: 4.3 / Motivation: 7
Selected for Mastercard Start Path Emerging Fintech program.
Raised $5.2M.
Founded 2019, based in Seattle/Sammamish WA.

**Two products:**
1. **ACF (Agentic Commerce Framework)** — governance standard they authored
2. **Firmly Connect** — launched March 2026. No-code platform abstracting MCP, AP2, ACP, UCP, A2A, KYA, TAP. Merchants connect once, distribute to any agent channel. Live customers: Best Buy, Backcountry.

**Additional products (from deck):**
- Agent Reputation Manager: behavior scoring across merchants to reduce fraud
- Agent Control Center: merchant dashboard to approve/restrict agent and channel access
- Firmly ID: subdomain identity for humans (agent.firmly.ai/[id]), passkey-bound via LoginID

**Firmly's stated moat (from deck):**
- Two-sided network effect: more identified humans attract more merchants, vice versa
- Accumulated data on human-agent relationships: scope patterns, trust signals, revocation history
- Merchant network behind the credential compounds with each new merchant
- Perimeter vendors (Akamai, F5, Cloudflare) as distribution channel

**Honest gap:** The human-enrollment side of the flywheel barely exists yet. Merchant side is live; "more humans attract more merchants" loop has not started.

**Damien's framing (WhatsApp June 11):** Fast no-code onboarding, show Mastercard live, then go Visa. Playing both networks against each other. Still in discussion with Visa. Countering ICC with Mastercard live traction.

---

## LoginID

FIDO2/WebAuthn biometric authentication. Core product: bind human identity to a phishing-resistant hardware/biometric credential.

Current customer: merchants, financial institutions, SaaS platforms (B2B).
Strategic question 2026: how does human biometric identity extend to agents acting on behalf of humans?

**Key value in agentic context:**
- Non-repudiation as a Service: hardware-attested, FIDO2-bound record that a specific human authorized a specific agent action. Cannot be spoofed or disclaimed.
- Mandate attestation: binding AP2 mandate creation to a LoginID biometric event makes mandates legally defensible.
- Velocity anomaly detection: LoginID holds the original authorization event and can detect if agent transaction velocity exceeds what the human authorized.
- Verified Buyer Network: directory of buyer agents whose human operators have completed LoginID FIDO2 enrollment.

---

## Damien Balsan

Chairman of the board of both Firmly and LoginID.
Santiago presented the Firmly+LoginID deck to him and the team on June 11, 2026.

Damien's WhatsApp message (June 11): "fast onboarding no code and show mastercard live and go visa" — meaning: Firmly's pitch to Visa is to arrive with Mastercard live traction as leverage. Playing both networks against each other.

---

## The Firmly + LoginID Deck

File: docs/LoginID-Firmly eval.md (Santiago's phase-by-phase advisory analysis, May 2026)
Deck: firmly_loginid_deck_final.html (presented June 11, 2026)

Title: "Firmly + LoginID: Building the Trust Layer for Agentic Commerce"

Six building blocks in the proposal:
1. NANDA — open agent registry, discovery layer
2. Business Agent Identity — DNSid + LoginID (corporate agents)
3. Human Agent Identity — Firmly ID + DNSid + LoginID (individual agents)
4. AP2 v0.2.0 — spending mandate engine
5. x402 — micropayment rail for catalog monetization
6. Seller Authorization Manifest — merchant-signed scope boundaries

Ten problems the stack addresses (grouped by Clerk's 4 auth questions):
- Identity: no stable human identity anchor, no agent-to-owner binding, discovery via single intermediary, legitimate agents blocked at perimeter, no seller agent legitimacy verification
- Scoping: buyer agent exceeds authorization, agents consume data at zero cost
- Approvals: no audit trail from human to agent to transaction
- Enforcement: no real-time credential revocation, no standardized agent receipt

Mastercard pitch (Slide 19): "Firmly and LoginID are the production stack that unlocks Agent Pay today — no bank implementation cycles required. The same case applies to Visa TAP — the network that moves first sets the standard."

Three additional markets identified: Buying Agents (demand side), Open Data (financial/health/legal), Corporate Task Delegation (enterprise).

**Deck caveat:** Written before June 10. Some claims marked "Complete" may be roadmap items internally. Human-enrollment flywheel is aspirational, not live.

---

## SupplyMind Phase Alignment with the News

| Phase | Protocol | Relevance |
|---|---|---|
| Phase 3 (A2A + x402) | x402 | Co-governed by Visa; production path confirmed |
| Phase 4/9 (AP2 Mandate Engine) | AP2 | Mastercard confirmed AP2 Mandates = valid Verifiable Intent |
| Phase 7 (secp256k1, DID) | Identity crypto | Ed25519/secp256k1 is exactly what TAP uses |
| Phase 12 (ACP checkout) | ACP | OpenAI agent surface now runs ACP |
| Phase 14 (Visa TAP, Mastercard Agent Pay) | TAP + Agent Pay | Current phase — priority just increased |

Phase 14 implementation targets:
1. TAP signature generation in Buyer Agent (RFC 9421 Ed25519 Signature-Input + Signature headers)
2. TAP signature verification in Seller Agent (simulate Visa Agent Registry locally)
3. Mastercard Verifiable Intent simulation (serialize AP2 mandate as signed Intent Artifact)
4. Move spending cap enforcement to network layer (Seller Agent / payment server), not buyer agent logic

---

## Three Sharp Questions for Damien (prepared for June 11 meeting)

1. **On the neutrality moat:** "Your edge over ICC is that Visa can't credibly be network-neutral but you can. How durable is that? Once ICC is live and good enough, what stops a merchant from taking Visa's free bundled option?"

2. **On the two-network leverage:** "Playing Mastercard and Visa against each other works until one asks for exclusivity. If Visa says do the deal but drop the Mastercard-live messaging, what happens?"

3. **On standards vs. pipe:** "ACF is in the deck as a building block but not the headline. Is the long-term defensibility in owning ACF as the standard everyone has to comply with, or in being the best integration pipe? Because those are two different companies."

---

## Key Links

- Visa + OpenAI announcement: https://investor.visa.com/news/news-details/2026/Visa-Partners-with-OpenAI-to-Power-the-Next-Generation-of-AI-Commerce/default.aspx
- Visa ICC announcement: https://investor.visa.com/news/news-details/2026/Visa-Opens-the-Door-to-AI-Driven-Shopping-for-Businesses-Worldwide/default.aspx
- Visa TAP GitHub: https://github.com/visa/trusted-agent-protocol
- Mastercard Agent Pay for Machines: https://www.mastercard.com/us/en/news-and-trends/press/2026/june/mastercard-launches-agent-pay-for-machines.html
- Mastercard Verifiable Intent: https://www.mastercard.com/global/en/news-and-trends/stories/2026/verifiable-intent.html
- Agent Payment Protocols Landscape: https://github.com/Custena/agent-payment-protocols
- Firmly Connect launch: https://finance.yahoo.com/sectors/technology/articles/firmly-launches-firmly-connect-first-130000538.html
- SiliconAngle Visa+OpenAI: https://siliconangle.com/2026/06/10/visa-partners-openai-let-ai-agents-make-payments-users/
