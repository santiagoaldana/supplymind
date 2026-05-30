# LoginID + Firmly: Phase-by-Phase Advisory Analysis

**Author:** Santiago Aldana
**Date:** May 2026
**Context:** Santiago is an advisor to both LoginID and Firmly. This document
evaluates each SupplyMind phase for relevance to their individual and joint
value proposition, using seven criteria to assess roadmap fit.

---

## Company Profiles

**LoginID** -- FIDO2/WebAuthn biometric authentication. Core product: bind human
identity to a phishing-resistant hardware/biometric credential. Strategic question
for 2026: how does human biometric identity extend to the agents acting on behalf
of that human?

**Firmly** -- Agentic commerce platform. Two products: ACF (the Agentic Commerce
Framework governance standard) and Firmly Connect (launched March 2026), a no-code
platform that abstracts across MCP, AP2, ACP, UCP, A2A, and KYA so merchants
connect once and distribute everywhere. Best Buy and Backcountry are live customers.
Strategic position: the horizontal infrastructure layer above all agentic commerce
protocols.

---

## The Correct Mental Model: Buyer Side vs. Merchant Side

This distinction is critical for understanding where each company's product sits
and where the value proposition lands.

**LoginID operates on the buyer side.**
LoginID's product authenticates the human who is delegating spending authority to
a buyer agent -- the CFO, procurement manager, or consumer who says "this agent
may purchase on my behalf." LoginID answers the question: is a verified human
behind this agent?

**Firmly operates on the merchant (seller) side.**
Firmly's customer is the merchant. Firmly Connect is the infrastructure the
merchant deploys to accept purchases from any buyer agent across any protocol.
Firmly answers the question: can my merchant safely and efficiently transact with
any incoming buyer agent?

**The value flows across the boundary.**
LoginID's buyer-side product creates value for Firmly's merchant customers.
A merchant using Firmly Connect benefits when buyers show up with LoginID-verified
identities -- reduced fraud, lower dispute liability, higher trust scores for
autonomous transactions.

**The 3D Secure analogy:**
3D Secure is the closest existing model. The card issuer (buyer's bank) authenticates
the cardholder during checkout. The merchant does not deploy 3D Secure -- the issuer
does. But the merchant is the primary beneficiary: lower fraud rates, chargeback
protection, regulatory coverage. LoginID is the issuer-side authenticator for the
agentic commerce era. Firmly is the merchant-side acceptance infrastructure.

**What this means for each phase analysis:**
The LoginID column in each phase distinguishes two things:
- **Buyer-side product**: what LoginID sells to buyer agent operators (enterprises,
  consumers delegating to agents)
- **Merchant-side value**: why Firmly's merchant customer cares that LoginID exists

The joint product is the enforcement surface where both meet: LoginID-verified
buyers get preferential treatment (lower friction, higher spending limits, faster
checkout) at merchants using Firmly Connect. Unverified buyers face more friction
or rejection. This is identical to how card network trust scores work today.

---

## LoginID Merchant-Side Product Opportunities

LoginID's natural motion is selling to buyer-side operators: enterprises and
consumers who delegate spending authority to agents. But if that is the only
product, LoginID depends on Firmly (or another merchant platform) to convert
buyer-side adoption into merchant-side revenue. The question is: what can
LoginID sell directly to merchants, that merchants will write a check for?

The answer comes from understanding what merchants actually pay for: fraud
prevention, compliance coverage, dispute protection, and conversion rate
improvement. LoginID has a unique asset the merchant cannot get elsewhere --
the original human authorization record. Four product ideas follow.

---

### Product 1: Non-Repudiation as a Service

**The merchant problem:** An autonomous agent places a $50,000 order. Six weeks
later the buyer's company disputes it: "Our agent exceeded its mandate. We did
not authorize that purchase." The merchant has no proof the transaction was
authorized. They lose the dispute and the goods.

**What LoginID can sell:** A signed, timestamped, hardware-attested record that
a specific human -- verified by FIDO2 biometric -- authorized a specific agent
mandate before the transaction ran. This record is the merchant's evidence in a
dispute. "Your CFO touched their fingerprint to authorize this mandate at 2:14pm
on Tuesday. Here is the cryptographic proof, signed by their hardware key."

**Pricing model:** Per-transaction fee on high-value orders, or a monthly SaaS
subscription per merchant above a volume threshold. Analogous to how Stripe
charges for Radar -- a fee on top of the base payment processing that buys
fraud protection.

**Why LoginID and not anyone else:** No one else holds the original biometric
authorization record. The buyer's ERP system might log the mandate, but it is
software-generated and mutable. LoginID's FIDO2 attestation is hardware-bound
and cannot be backdated or altered. That is the evidence quality a court or
financial regulator accepts.

**Where it shows in SupplyMind:** Phase 9 AP2 v0.2.0 Intent Mandates carry a
`signed_by` field. If LoginID signs that field, every Cart Mandate downstream
inherits the non-repudiation chain. The merchant receives the full chain:
biometric (LoginID) -> mandate (AP2 v0.2.0) -> transaction (x402).

---

### Product 2: Compliance Attestation Certificate

**The merchant problem:** A credit union, government agency, or regulated
retailer needs to prove to an auditor that every autonomous purchase in the
prior 12 months was authorized by a verified human with appropriate spending
authority. Today there is no standard artifact for this. The auditor sees
transactions but no authorization chain.

**What LoginID can sell:** A per-mandate or per-period compliance certificate:
"Human X (role: CFO, verified by FIDO2 hardware credential, LoginID credential
ID: abc123) authorized Agent Y (DID: did:web:acme.com:procurement) to spend up
to $Z per transaction in category W. Authorization event: ISO8601 timestamp.
Certificate issued by: LoginID Inc."

This is a **regulated product**, not just a technical feature. It is the
agentic-commerce equivalent of a SOX control or a PCI DSS compliance report.
It gives the merchant's CISO a printable artifact for the annual audit.

**Pricing model:** Annual subscription per merchant, priced by audit volume
(number of mandates certified per year). Higher price tier for financial
services and government segments where the regulatory requirement is explicit.

**Why this is defensible:** Compliance attestation requires being the authority
that issued the credential. A third party cannot retroactively certify that
a human authorized something -- only the authentication provider who ran the
biometric challenge holds the original attestation record. LoginID's position
as the issuer is the moat.

**Where it shows in SupplyMind:** Phase 10 Governance Dashboard. The CISO
artifact section would pull LoginID compliance certificates as part of the
mandate ledger view. Firmly surfaces it; LoginID issues it.

---

### Product 3: Agent Velocity Monitoring (Anomaly Signal Feed)

**The merchant problem:** A buyer agent is authorized to spend $500/month on
office supplies. Three weeks in, it has placed 40 orders totaling $12,000.
Either the mandate was misconfigured, or the agent was compromised, or someone
changed the mandate without the original authorizing human's knowledge. The
merchant sees the transactions but has no baseline to compare against.

**What LoginID can sell:** A real-time anomaly signal: is this agent's
transaction velocity consistent with what its human authorized? LoginID holds
the original mandate authorization record -- the biometric event, the spending
bounds, the approved vendor list. LoginID can compute: this agent is running at
24x the authorized rate. That is an anomaly signal the merchant gets as an API
call or a webhook before the next transaction clears.

This is **the only fraud signal the merchant cannot build themselves**, because
it requires comparing live transaction behavior against the original
authorization event -- and only LoginID has that event.

**Pricing model:** Per-merchant SaaS subscription, tiered by number of monitored
agent mandates. Premium tier includes real-time webhook alerts; standard tier
is a daily digest. Similar to how Stripe Radar is sold -- a fraud prevention
layer on top of the payment infrastructure.

**Where it shows in SupplyMind:** Phase 14 (Fraud and Bot Detection). The
anomaly feed in the Governance Dashboard would include LoginID velocity signals
alongside DNSid rate limiting and Stripe Radar signals. Three independent
signals converging on the same anomaly is the detection architecture.

---

### Product 4: Verified Buyer Network (Access Fee Model)

**The merchant problem:** Not all buyer agents are equal. Some represent
Fortune 500 procurement departments with real mandates and real accountability.
Others are scripts running with no human oversight. The merchant wants to give
better terms -- lower prices, higher order limits, faster approval -- to the
first category. But there is no way to tell them apart today.

**What LoginID can sell:** Membership in a **Verified Buyer Network**: a
directory of buyer agents whose human operators have completed LoginID FIDO2
enrollment. Merchants pay a monthly access fee to query the network before
processing a purchase. A buyer in the network gets a trust score; a buyer
outside the network gets default (lower) trust.

This is the **Visa/Mastercard model applied to agents**: the card network charges
merchants an interchange fee because the network brings verified, solvent
cardholders. LoginID charges merchants an access fee because the network brings
verified, accountable agents.

**Pricing model:** Monthly access fee per merchant, plus a per-query fee for
real-time trust score lookups. Volume discounts for high-transaction merchants.
This is a network-effect business: the more buyers enroll, the more valuable
the network is to merchants, the more merchants pay the access fee, the more
buyers have an incentive to enroll.

**Why Firmly is the distribution partner, not the competitor:** Firmly Connect
is the integration surface that makes the network lookup automatic for merchants.
LoginID does not need to build a merchant portal -- they need to embed the
network query into Firmly's purchase flow. Firmly gets a better product (trust
scoring for every buyer); LoginID gets distribution to every Firmly merchant
without a direct sales motion. This is the joint product that neither can
build alone.

**Where it shows in SupplyMind:** Phase 8 already has the gate architecture --
the `X-Agent-DNSid` header and the `buyer_dnsid_verified` flag are the technical
skeleton. The Verified Buyer Network is the business model that sits on top of
that architecture: the flag is worth something because there is a paid network
behind it.

---

### Summary: Four Merchant-Side Products for LoginID

| Product | What the merchant pays for | Analogy | Joint with Firmly? |
|---------|---------------------------|---------|-------------------|
| Non-Repudiation as a Service | Dispute protection on high-value agent orders | Stripe Radar fraud protection | Yes -- dispute artifacts flow through Firmly Connect |
| Compliance Attestation Certificate | Auditor-grade proof of human authorization | SOC 2 report, PCI DSS attestation | Yes -- surfaces in Phase 10 dashboard |
| Agent Velocity Monitoring | Fraud signal: agent exceeding authorized scope | Stripe Radar anomaly detection | Yes -- feeds into Phase 14 fraud layer |
| Verified Buyer Network | Access to accountable, human-backed buyer agents | Visa/Mastercard interchange model | Yes -- Firmly is the distribution surface |

The common thread: LoginID's moat is **holding the original authorization
record** that no one else has. Every merchant-side product is a derivative
of that record -- dispute protection, compliance proof, anomaly detection,
or trust scoring. The buyer-side enrollment is the input; these four products
are the output that merchants pay for.

---

## Evaluation Criteria

1. **Differentiation** -- does this give LoginID or Firmly a capability no
   competitor currently offers?
2. **Gap addressed** -- is this problem genuinely unsolved, or is a dominant
   solution already emerging?
3. **Standard clarity** -- is the protocol settled enough to build on, or still
   contested?
4. **Wedge position** -- does being early here create a defensible moat, or is
   it easily replicated once the standard settles?
5. **Joint leverage** -- is this a place where LoginID + Firmly together are
   uniquely positioned versus either alone?
6. **Regulatory tailwind** -- is there a compliance or liability driver
   accelerating adoption of this layer?
7. **Enterprise sales motion fit** -- does this give a CISO or CFO a concrete
   artifact they can approve and audit?

---

## Phase 1: MCP Servers

| Criterion | LoginID | Firmly |
|-----------|---------|--------|
| Differentiation | Low | None |
| Gap addressed | MCP auth gap is real but LF MCP Auth is already working on it | Already covered by Firmly Connect |
| Standard clarity | High -- MCP has won this layer | High |
| Joint leverage | Low | Low |
| Regulatory tailwind | Low | Low |
| Enterprise sales fit | Low | Low |

**LoginID:** MCP has no native auth layer -- any agent that reaches an MCP server
can call any tool. LoginID could offer MCP server authentication by binding tool
access to the human operator's FIDO2 credential. The human who deployed the MCP
server vouches for it via biometric. This is a real gap. However, Linux Foundation's
MCP Auth initiative is already working on this, which reduces the differentiation window.

**Firmly:** Firmly Connect already abstracts MCP as one of its supported protocols.
No new roadmap item needed.

**Roadmap recommendation:** LoginID -- monitor MCP Auth spec; position as the
biometric binding layer for MCP server operators if the spec leaves room for it.
Firmly -- already covered.

---

## Phase 2: UCP Catalog

| Criterion | LoginID | Firmly |
|-----------|---------|--------|
| Differentiation | None | Medium |
| Gap addressed | No direct play | Catalog signing is genuinely unsolved |
| Standard clarity | High | High -- Google/Walmart/Shopify coalition standard |
| Joint leverage | Low | Low |
| Regulatory tailwind | Low | Low |
| Enterprise sales fit | Low | Medium |

**LoginID:** No direct play. UCP is a catalog format, not an identity layer.

**Firmly:** The real gap here is catalog signing -- nothing in the UCP spec prevents
a man-in-the-middle from serving a modified catalog with inflated prices or
fraudulent SKUs. Firmly, sitting as the horizontal layer between merchants and
agents, is the natural place to sign catalog documents on behalf of merchants,
giving buyer agents a trust anchor before they parse any catalog data. This is a
differentiated, unsolved problem that Firmly's position uniquely enables.

**Roadmap recommendation:** Firmly -- add catalog document signing as a feature
of Firmly Connect. Merchant publishes catalog through Firmly; Firmly signs it with
the merchant's key; buyer agents verify the signature before trusting catalog data.
Turns a UCP security gap into a Firmly Connect feature.

---

## Phase 3: A2A + x402

| Criterion | LoginID | Firmly |
|-----------|---------|--------|
| Differentiation | High (Agent Card signing) | Medium (x402 governance) |
| Gap addressed | Agent Card spoofing is unsolved | x402 replay attacks are unsolved |
| Standard clarity | A2A maturing | x402 maturing |
| Joint leverage | Medium | Medium |
| Regulatory tailwind | Low | Low |
| Enterprise sales fit | Medium | Medium |

**LoginID (buyer-side product):** A2A v1.2 added signed Agent Cards but the signing
infrastructure is not standardized. LoginID could offer Agent Card signing for
buyer agent operators -- the enterprise or consumer running a buyer agent signs
their Agent Card with a FIDO2-backed credential, proving a verified human vouches
for that agent. Right now buyer Agent Cards are self-asserted by whoever deployed
the agent.

**LoginID (merchant-side value):** A seller using Firmly Connect can require or
prefer buyer agents whose Agent Cards are LoginID-signed. The x402 gate becomes
trust-tiered: LoginID-verified buyers get the free quote threshold raised (less
friction); unverified buyers hit the x402 wall sooner. The merchant sets this
policy once in Firmly Connect; LoginID's credential does the discrimination.

**Firmly:** x402 payment challenges have no signing requirement -- a man-in-the-middle
can substitute their own wallet address. Firmly, sitting between merchant and agent,
signs x402 payment challenges on behalf of merchants. Firmly Connect's agent
allowlist enforces which buyers can initiate payment flows, with LoginID verification
as an optional trust tier.

**Joint:** LoginID-verified buyer agents get a smoother x402 experience at any
Firmly Connect merchant. Unverified buyers pay more friction or get blocked.
The merchant controls the policy; LoginID provides the signal.

**Roadmap recommendation:** LoginID -- Agent Card signing service for buyer agent
operators. Firmly -- trust-tiered x402 policy in Firmly Connect (LoginID-verified
buyers get higher free-quote threshold).

---

## Phase 4: AP2 + ACF + MPP

| Criterion | LoginID | Firmly |
|-----------|---------|--------|
| Differentiation | Very high | Very high |
| Gap addressed | Unsigned mandates, no human attestation | ACF tiers as code constants, no signed policy |
| Standard clarity | AP2 maturing; ACF is Firmly's own standard | High |
| Joint leverage | Very high | Very high |
| Regulatory tailwind | High | High |
| Enterprise sales fit | Very high | Very high |

**LoginID (buyer-side product):** The AP2 mandate is set by the human who controls
the buyer agent -- the CFO or procurement manager who says "my agent may spend up
to $500 per transaction." LoginID's play is here: bind the creation of the AP2
Intent Mandate to a FIDO2 biometric challenge on the buyer side. The human
authenticates with their fingerprint or hardware key to sign the mandate. The mandate
is now human-vouched and hardware-attested -- not just policy in code.

**LoginID (merchant-side value):** When a buyer agent presents a Cart Mandate linked
to a LoginID-attested Intent Mandate, the seller has cryptographic proof that a
verified human set the spending bounds. This is the mandate provenance signal the
merchant needs for high-value autonomous transactions. A buyer agent without this
attestation gets treated as higher risk -- tighter ACF tiers, lower AUTO thresholds,
or manual review.

**Firmly:** ACF is Firmly's own standard. Firmly Connect is the enforcement surface.
Firmly should position the Agent Control Center as the mandate management UI for
merchants: merchants set ACF tiers and vendor allowlists visually, Firmly generates
signed AP2 mandates, and the dashboard shows which incoming buyer mandates are
LoginID-attested vs. unattested. This is the complete governance artifact for a
CISO or CFO.

**Joint:** The mandate attestation ceremony is the joint product. LoginID handles
the biometric signing on the buyer side. Firmly enforces the policy and surfaces
attestation status on the merchant side. Neither can deliver the complete enterprise
compliance story without the other.

**Roadmap recommendation:** Highest priority joint initiative. LoginID + Firmly
co-develop "Human Attestation for Agent Mandates." LoginID sells to buyer agent
operators (enterprises running procurement agents). Firmly integrates LoginID
attestation signals into the Agent Control Center merchant dashboard.

---

## Phase 5: Protocol Reflection + Second Seller

No direct product relevance for either company. Skip.

---

## Phase 6: NANDA Discovery

| Criterion | LoginID | Firmly |
|-----------|---------|--------|
| Differentiation | Medium | None |
| Gap addressed | NANDA registration is self-asserted | Already covered by Firmly Connect |
| Standard clarity | Experimental | Experimental |
| Joint leverage | Low | Low |
| Regulatory tailwind | Low | Low |
| Enterprise sales fit | Low | Low |

**LoginID:** NANDA registrations are self-asserted -- any agent can claim any
capability. LoginID could offer verified NANDA registration: a merchant proves
their identity via FIDO2 before their agent is registered, and LoginID co-signs
the AgentFacts document. Creates a two-tier NANDA registry: unverified listings
and LoginID-verified listings. Buyer agents could filter to only discover verified
sellers.

**Firmly:** Firmly Connect's catalog distribution is a superset of NANDA.
No specific roadmap item needed.

**Roadmap recommendation:** LoginID -- verified NANDA registration as a trust tier.
Low urgency given experimental status of NANDA. Firmly -- already covered.

---

## Phase 7: Cryptographic Identity (secp256k1, DID, KYA)

| Criterion | LoginID | Firmly |
|-----------|---------|--------|
| Differentiation | Very high | None |
| Gap addressed | Key-to-owner binding is asserted not proven; no revocation | No direct play |
| Standard clarity | DID:web mature; KYA pattern emerging | N/A |
| Joint leverage | Medium | Low |
| Regulatory tailwind | Medium | Low |
| Enterprise sales fit | High | Low |

**LoginID:** This is LoginID's home territory approached from a new angle. The
secp256k1 key is currently generated in software and stored in a file. LoginID's
value is binding that key to a hardware-backed biometric credential so the key
cannot be extracted or transferred without the human's physical presence. LoginID
should offer a KYA document signing service where the agent's private key is
protected by a FIDO2 authenticator -- the agent key lives in hardware, not a
.hex file. This transforms KYA from "we claim this key belongs to us" to "this
key is hardware-bound to a verified human and cannot be exfiltrated."

**Firmly:** No direct play at the cryptographic identity layer. Firmly benefits
as a consumer of strong identity but does not need to build it.

**Joint:** LoginID provides hardware-protected agent keys. Firmly uses those keys
to sign mandates. The chain becomes: human biometric (LoginID) attests to both
the agent's identity and the agent's spending policy (Firmly). Single attestation
ceremony, dual coverage.

**Roadmap recommendation:** LoginID -- hardware-backed agent key management as a
product. Position as "FIDO2 for agents" -- the same guarantee FIDO2 gives for
human credentials, now for agent credentials.

---

## Phase 8: DNSid Ownership Layer

| Criterion | LoginID | Firmly |
|-----------|---------|--------|
| Differentiation | High | Medium |
| Gap addressed | Key-to-owner binding, revocation -- genuinely unsolved | Agent registry ownership awareness |
| Standard clarity | Experimental -- launched April 2026 | Experimental |
| Joint leverage | Medium | Medium |
| Regulatory tailwind | High | Medium |
| Enterprise sales fit | High | High |

**LoginID (buyer-side product):** DNSid anchors buyer agent ownership to a DNS
domain. LoginID anchors it one layer deeper: to a biometric-verified human identity.
DNSid says "this domain controls this agent." LoginID says "this verified human
controls this domain and this agent." LoginID should pursue integration with
Identity Digital (DNSid) to become the human attestation layer on top of DNSid
registration -- when a buyer agent operator registers on DNSid, LoginID provides
the FIDO2 verification of the registrant.

**LoginID (merchant-side value):** A buyer agent that presents a DNSid handle
registered via LoginID gives the merchant a complete accountability chain: which
human, verified by biometric, owns the agent making this purchase. This is the
signal Firmly Connect surfaces in the Agent Control Center -- verified vs.
unverified buyer agent ownership at a glance.

**Firmly:** Firmly Connect's agent allowlist should resolve buyer DNSid handles
before accepting any agent connection. Merchants see ownership status for every
connected buyer agent. The gate is configurable: default-off today (most buyer
agents have no DNSid handle yet), turned on as the ecosystem matures.

**Roadmap recommendation:** LoginID -- DNSid + FIDO2 registration integration.
Firmly -- DNSid resolution in Firmly Connect agent registry with configurable
trust-gating policy for merchants.

---

## Phase 9: AP2 v0.2.0 Signed Mandates

| Criterion | LoginID | Firmly |
|-----------|---------|--------|
| Differentiation | Very high | Very high |
| Gap addressed | Who signs Intent Mandates and how? -- genuinely unsolved | No one has early AP2 v0.2.0 compliance |
| Standard clarity | Experimental -- announced May 2026 | Experimental |
| Joint leverage | Very high | Very high |
| Regulatory tailwind | Very high | Very high |
| Enterprise sales fit | Very high | Very high |

**LoginID:** AP2 v0.2.0 signed Intent Mandates require a signer. The spec defines
the structure but not who holds the signing key or how the human proves they
authorized the signing. This is LoginID's most important roadmap item: be the
biometric signing ceremony for AP2 Intent Mandates. When a CFO or procurement
manager creates a mandate in Firmly Connect, LoginID handles the signing step --
Touch ID, Face ID, or hardware key. The mandate becomes a legally defensible
artifact: this human, verified by hardware biometric, authorized this spending
policy at this timestamp.

**Firmly:** AP2 v0.2.0 is the upgrade path for ACF mandates. Firmly should lead
with AP2 v0.2.0 compliance as the governance backbone of Firmly Connect -- the
mandate ledger in the Agent Control Center becomes the AP2 v0.2.0 audit trail.
Early compliance with a just-released spec is a meaningful differentiation signal
to enterprise buyers.

**Joint:** The Intent Mandate signing ceremony is the joint product. Firmly
generates the mandate structure; LoginID handles the human attestation. Neither
can fully deliver the enterprise compliance story without the other.

**Roadmap recommendation:** Highest priority joint initiative alongside Phase 4.
Design the signing UX together now while the AP2 v0.2.0 spec is still experimental
-- be the reference implementation.

---

## Phase 10: Governance Dashboard

| Criterion | LoginID | Firmly |
|-----------|---------|--------|
| Differentiation | Low (as contributor) | Very high |
| Gap addressed | No CISO-grade agentic commerce audit UI exists | No CISO-grade agentic commerce audit UI exists |
| Standard clarity | N/A -- application layer | N/A |
| Joint leverage | Medium | Medium |
| Regulatory tailwind | Very high | Very high |
| Enterprise sales fit | Very high | Very high |

**LoginID:** Limited direct play. Could contribute a "human attestation log" panel
-- every mandate signed by a LoginID-verified human appears with the biometric
attestation timestamp. Strengthens the audit trail but is a data feed, not a
standalone product.

**Firmly:** The Agent Control Center is already this product at the merchant level.
The gap is the enterprise/CISO version: not just "which agents are selling my
products" but "who authorized each agent, what are their spending bounds, has
anything been revoked, are there anomalies." Firmly should build the CISO-grade
version of the dashboard as an enterprise tier of Firmly Connect, with full Clerk
four-question coverage (Identity, Scoping, Approvals, Enforcement status for every
connected agent).

**Roadmap recommendation:** Firmly -- enterprise governance tier of Agent Control
Center. Most valuable single product investment for enterprise sales motion.
LoginID -- human attestation log as a data feed into the dashboard.

---

## Phase 11: Multi-Protocol Checkout (ACP + UCP)

| Criterion | LoginID | Firmly |
|-----------|---------|--------|
| Differentiation | None | Very high -- this is Firmly Connect's core |
| Gap addressed | N/A | Protocol fragmentation is the current merchant pain |
| Standard clarity | Both maturing | Both maturing |
| Joint leverage | Low | Low |
| Regulatory tailwind | Low | Low |
| Enterprise sales fit | High | High |

**LoginID:** No direct play at the protocol routing layer.

**Firmly:** This is Firmly Connect's core product. Already executing. The
differentiation opportunity is being the first to certifiably support both
protocols with a compliance audit trail showing which protocol each transaction
used and which mandate governed it.

**Roadmap recommendation:** Firmly -- already executing. Add protocol-of-record
to the mandate audit trail. LoginID -- no action needed.

---

## Phase 12: Agent Wallet Layer

| Criterion | LoginID | Firmly |
|-----------|---------|--------|
| Differentiation | High | Medium |
| Gap addressed | Wallet binding to verified human identity is unsolved | Single interface for all payment types |
| Standard clarity | Maturing | Maturing |
| Joint leverage | Medium | Medium |
| Regulatory tailwind | High -- financial regulators require KYC on wallet owners | High |
| Enterprise sales fit | High | High |

**LoginID:** Coinbase Agentic Wallet and Stripe Link wallets need to be bound to
a verified human identity for regulatory compliance. LoginID is the KYC/biometric
binding layer for agent wallets -- the wallet is provisioned only after the human
operator passes a FIDO2 authentication. This is directly analogous to LoginID's
existing business but applied to agent wallets rather than human logins. Financial
regulators will require this; LoginID can be ahead of the mandate.

**Firmly:** Firmly Connect's merchant-of-record model means Firmly holds the
payment relationship. Firmly should require LoginID biometric attestation as part
of wallet activation in Firmly Connect -- protects Firmly from regulatory exposure
and differentiates the platform as compliance-first.

**Roadmap recommendation:** LoginID -- agent wallet KYC binding as a product.
Firmly -- LoginID as required attestation step for wallet activation.

---

## Phase 13: Network Credential Layer (Visa TAP + Mastercard Agent Pay)

| Criterion | LoginID | Firmly |
|-----------|---------|--------|
| Differentiation | High | High |
| Gap addressed | Biometric consumer consent for network credentials is unsolved | No agentic platform natively validates both network credentials |
| Standard clarity | Maturing -- both networks live | Maturing |
| Joint leverage | High | High |
| Regulatory tailwind | Very high | Very high |
| Enterprise sales fit | Very high | Very high |

**LoginID:** Visa TAP requires a consumer consent record signed by the consumer's
issuer. Mastercard Verifiable Intent requires a tamper-resistant record of what
the human authorized. Neither requires biometric proof of the human during consent.
LoginID can be the biometric consent ceremony -- when a consumer grants an agent
permission to use their Visa or Mastercard, LoginID provides the FIDO2 attestation
that a verified human (not a script) gave that consent. Direct integration point
with both networks.

**Firmly:** Firmly Connect as merchant-of-record needs to accept Visa TAP and
MC Agent Pay credentials from buyer agents. Firmly should be the first agentic
commerce platform to natively validate both network credentials before accepting
any agent purchase -- turning this into a trust signal for merchants using
Firmly Connect.

**Joint:** LoginID provides the consumer consent biometric. Firmly validates the
resulting network credential. Full chain: human biometric (LoginID) -- network
token (Visa TAP / MC Agent Pay) -- merchant acceptance (Firmly Connect).

**Roadmap recommendation:** Highest regulatory urgency for both companies. Visa TAP
and MC Agent Pay integration should be prioritized for any customer in financial
services, banking, or regulated retail.

---

## Phase 14: Fraud and Bot Detection

| Criterion | LoginID | Firmly |
|-----------|---------|--------|
| Differentiation | Medium | Medium-High |
| Gap addressed | Agent traffic classification is genuinely unsolved | Network-level agentic fraud data is unavailable elsewhere |
| Standard clarity | Low -- no standard approach yet | Low |
| Joint leverage | High | High |
| Regulatory tailwind | Medium | Medium |
| Enterprise sales fit | High | High |

**LoginID:** LoginID's biometric binding creates a natural fraud signal -- any
agent presenting a credential not backed by a FIDO2 attestation is immediately
suspect. LoginID could offer a legitimacy score based on credential provenance:
hardware-backed biometric = high trust; software key = medium trust; no credential
= flag.

**Firmly:** Firmly Connect sees traffic from all agents connecting to its merchant
network. Firmly has the data to build an agentic traffic classifier -- valid
Firmly-verified merchant connection + AP2 mandate + DNSid handle = legitimate;
anything else = suspect. This is a network effect moat: the more merchants use
Firmly Connect, the better the traffic data, the better the classifier.

**Roadmap recommendation:** Firmly -- traffic classification as a network-effect
product built on Firmly Connect's merchant network. This becomes more valuable as
the merchant network grows. LoginID -- credential legitimacy score as an input to
Firmly's classifier.

---

## Phase 15: Stablecoin Settlement (x402 + AWS AgentCore)

| Criterion | LoginID | Firmly |
|-----------|---------|--------|
| Differentiation | Low | Medium |
| Gap addressed | x402 KYC binding is possible but not current requirement | Single-interface stablecoin + fiat is a merchant convenience |
| Standard clarity | Experimental | Experimental |
| Joint leverage | Low | Low |
| Regulatory tailwind | Medium -- may increase | Medium |
| Enterprise sales fit | Medium | Medium |

**LoginID:** No direct play unless regulators require biometric KYC for stablecoin
wallet access (possible but not current). Monitor.

**Firmly:** Firmly Connect handling stablecoin settlement as a rail option alongside
fiat gives merchants a single interface for all payment types. Low urgency given
experimental status.

**Roadmap recommendation:** Both -- monitor and revisit when x402 moves from
experimental to maturing.

---

## Joint Value Proposition Summary

| Layer | LoginID | Firmly | Joint |
|-------|---------|--------|-------|
| Human attestation | FIDO2 biometric for mandate signing | Mandate generation UI | Biometric-attested AP2 Intent Mandate |
| Agent identity | Hardware-backed agent keys | DNSid resolution in merchant registry | FIDO2-protected agent credential |
| Spending governance | Biometric approval ceremony | ACF tiers + AP2 mandate engine | Human-vouched spending policy |
| Audit trail | Human attestation log | Agent Control Center | CISO-grade compliance dashboard |
| Network credentials | Biometric consumer consent for Visa TAP / MC Agent Pay | Network credential validation in Firmly Connect | Full chain from human to network token |

---

## Priority Matrix

| Priority | Initiative | Owner | Phase |
|----------|-----------|-------|-------|
| 1 | Human Attestation for Agent Mandates (joint product) | LoginID + Firmly | 4, 9 |
| 2 | CISO-grade enterprise governance dashboard | Firmly | 10 |
| 3 | Visa TAP + Mastercard Agent Pay integration | Both | 13 |
| 4 | Hardware-backed agent key management ("FIDO2 for agents") | LoginID | 7 |
| 5 | Agent wallet KYC binding | LoginID | 12 |
| 6 | DNSid + FIDO2 human accountability chain | LoginID | 8 |
| 7 | Catalog document signing in Firmly Connect | Firmly | 2 |
| 8 | Agent Card signing service | LoginID | 3 |
| 9 | Verified NANDA registration tier | LoginID | 6 |
| 10 | x402 / stablecoin settlement | Both | 15 |

---

## The Single Framing Sentence

LoginID proves the human behind the agent. Firmly governs what the agent can do.
Together they are the only platform that can produce a biometric-attested,
cryptographically signed, CISO-auditable record of every autonomous commercial
action -- from the human who authorized it to the transaction that executed it.

The gap no competitor currently addresses: Clerk's analysis identifies enforcement
as the weakest layer across the entire industry in mid-2026. The joint LoginID +
Firmly product is the closest thing currently achievable to a real enforcement
engine -- not just policy in code, but policy attested by a human, signed
cryptographically, and auditable by a regulator. That is the enterprise wedge.
