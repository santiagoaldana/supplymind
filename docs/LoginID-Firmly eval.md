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

## The Correct Mental Model: Both Companies Sell to the Merchant

**The shared customer is the merchant.**

LoginID is a B2B company. Their current business is selling to enterprises --
merchants, financial institutions, and SaaS platforms -- that deploy LoginID to
authenticate their own users and customers. The "buyer-side operator" market
(enterprises running procurement agents that need to credential those agents with
LoginID) is largely theoretical in mid-2026. That market will exist as agentic
commerce matures, but it cannot be the basis for a joint product roadmap today.

**Firmly's customer is the merchant.** Firmly Connect is the infrastructure
merchants deploy to accept purchases from any buyer agent across any protocol.

**LoginID's current customer is also the merchant** -- enterprises that want to
protect their own systems, their own agent configurations, and their own liability
exposure from unauthorized agentic activity.

The joint product is therefore: what can LoginID and Firmly sell together to the
same merchant, that neither can deliver alone?

**What merchants pay for today:**
- Fraud prevention with direct dollar ROI (chargeback reduction)
- Compliance coverage (auditor artifacts, regulatory liability reduction)
- Dispute protection on high-value transactions
- Operational simplification (fewer integration points, less configuration surface)

**Where Gmail authentication is not enough -- the key pricing question:**
Gmail OAuth verifies "this human has access to this email account." It cannot
prove "this human, with their physical body present, deliberately authorized
this specific commercial action." There are three contexts where that gap has
dollar value attached:

1. **Liability transfer on large autonomous transactions.** When an agent places
   a $50,000 order and the buyer later disputes it, the merchant needs a chain of
   evidence that holds up legally. FIDO2 biometric provides hardware attestation --
   the private key never leaves the device, the biometric was required to unlock it,
   the timestamp is signed. Gmail provides none of this. The merchant pays for
   dispute protection, not authentication.

2. **Regulated industries where authorization trails are mandatory.** Credit
   unions, government suppliers, pharmaceutical distributors operate under compliance
   frameworks (SOX, FedRAMP, procurement regulations) where every material financial
   decision needs a signed authorization record. A Gmail login is an access event,
   not an authorization event. LoginID's biometric sign-off is an authorization
   event with cryptographic proof. The auditor accepts one and not the other.

3. **Agentic transactions where "who approved this, right now" cannot be verified
   by other means.** An agent presents credentials and claims to act within a human's
   authorization. Gmail can prove a human set up an account once. It cannot prove
   that authorization is current, within scope, and has not been revoked. FIDO2
   provides a live, hardware-attested proof of intent at the moment of authorization.

**What this means for each phase analysis:**
The LoginID column evaluates: does this phase create a context where the merchant
needs authorization-quality proof that Gmail cannot provide? The Firmly column
evaluates: does this phase give Firmly a stronger merchant product when LoginID
is integrated? The joint column identifies where both questions answer yes.

**Future evolution (as agentic commerce matures):**
As enterprises begin deploying and credentialing their own buyer agents at scale,
a second market opens: buyer-side operators who need to prove their agents are
accountable. LoginID is well positioned for that market when it arrives. The joint
products in that phase will serve the buyer operator rather than the merchant --
but that is a 2027+ motion, not today's product roadmap.

---

## LoginID Merchant-Side Product Opportunities

LoginID's current customer is the merchant -- enterprises and platforms that
deploy LoginID to protect their own systems. The question is: what specifically
can LoginID sell to a merchant in the agentic commerce context, where the merchant
is already paying Firmly for protocol infrastructure?

LoginID's unique asset is the original authorization record -- a hardware-attested,
biometrically-signed proof that a specific human approved a specific action. No
other vendor holds this record. Every merchant-side product is a derivative of it.

---

### Product 1 (Merchant Controls Their Own Agents -- Lower Priority)

> *Note: A merchant deploying a seller agent needs that agent credentialed. LoginID
> could offer the biometric authorization ceremony for agent deployment -- the CISO
> or CTO signs off on the agent configuration with their hardware credential.
> However, this may not be a strong standalone product: merchants today deploy
> websites and APIs without identity ceremonies, and the incremental willingness
> to pay for agent credentialing is unclear. The products below have clearer
> dollar ROI for the merchant and are higher priority. This category may become
> more relevant as regulatory requirements for agent deployment mature.*

---

### Product 2 (renamed from 1): Non-Repudiation as a Service

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

### Product 3 (renamed from 2): Compliance Attestation Certificate

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

### Product 4 (renamed from 3): Agent Velocity Monitoring (Anomaly Signal Feed)

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

### Product 5 (renamed from 4): Verified Buyer Network (Access Fee Model -- Future)

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

### Summary: Merchant-Side Products for LoginID

| Priority | Product | What the merchant pays for | Analogy | Joint with Firmly? |
|----------|---------|---------------------------|---------|-------------------|
| High now | Non-Repudiation as a Service | Dispute protection on high-value agent orders | Stripe Radar fraud protection | Yes -- artifacts flow through Firmly Connect |
| High now | Compliance Attestation Certificate | Auditor-grade proof of human authorization | SOC 2 report, PCI DSS attestation | Yes -- surfaces in Phase 10 dashboard |
| High now | Agent Velocity Monitoring | Fraud signal: agent exceeding authorized scope | Stripe Radar anomaly detection | Yes -- feeds into Phase 14 fraud layer |
| Future | Verified Buyer Network | Access to accountable, human-backed buyer agents | Visa/Mastercard interchange model | Yes -- Firmly is the distribution surface |
| Lower priority | Agent Deployment Credentialing | Compliance ceremony for merchant's own agent setup | N/A -- no strong precedent | Yes -- Firmly Connect onboarding |

The common thread: LoginID's moat is **holding the original authorization
record** that no other vendor has. Every merchant-side product is a derivative
of that record -- dispute protection, compliance proof, anomaly detection, or
trust scoring. The products with the clearest merchant willingness to pay today
are the ones with a direct liability or regulatory driver: Non-Repudiation and
Compliance Attestation. The Verified Buyer Network becomes the highest-value
product as the buyer-agent market matures -- it is the network-effect business,
but it requires buyer-side adoption that does not yet exist at scale.

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

**Roadmap recommendation:** Highest priority joint initiative. The merchant is
the shared customer. Firmly sells the mandate management UI and ACF governance;
LoginID sells the authorization ceremony that makes mandates legally defensible.
The product pitch to the merchant: "Firmly + LoginID gives you a mandate your
lawyer can use in a dispute and your auditor can stamp."

---

## Phase 5: Protocol Reflection + Second Seller

No direct product relevance for either company. Skip.

---

## Phase 6: NANDA Discovery + Maritime Hosting

| Criterion | LoginID | Firmly |
|-----------|---------|--------|
| Differentiation | High | High -- underweighted in prior analysis |
| Gap addressed | Registry self-assertion is a fraud surface; verified listings do not exist | No agentic commerce platform has a verified agent directory as a product |
| Standard clarity | Experimental -- but NANDA is the only open W3C-VC registry | Experimental |
| Joint leverage | Very high | Very high |
| Regulatory tailwind | Medium | Medium |
| Enterprise sales fit | High | High |

**What NANDA is and why it matters more than previously scored:**

NANDA (Project NANDA) is the decentralized agent registry where agents publish
their capabilities as W3C Verifiable Credentials -- AgentFacts documents. It is
the DNS of the agentic web: a buyer agent that doesn't know a seller's URL can
search NANDA by capability tag and get a list of candidates. SupplyMind is
registered on NANDA (HTTP 201 confirmed, Phase 6). The structure is
production-ready; the only missing piece is a public HTTPS host.

The security problem with NANDA today: any agent can register claiming any
capability. There is no verification layer. A malicious seller agent can
register as "certified office supplies distributor" and appear in search results
alongside legitimate sellers. Buyer agents have no way to distinguish a
self-asserted claim from a verified one at discovery time.

**What Maritime is:**

Maritime.sh is a cloud hosting platform purpose-built for AI agents -- roughly
$1/month per agent. It provides a public HTTPS endpoint (which NANDA requires),
automatic agent card generation, and agent discovery services. It is the lowest
friction path from "I have a local agent" to "my agent is live on the open
agentic web." SupplyMind built a Maritime deployment manifest in Phase 6. One
deploy command moves SupplyMind from localhost to a publicly reachable, NANDA-
registered, HTTPS-hosted agent.

Maritime is not just a hosting convenience -- it is a distribution mechanism.
An agent hosted on Maritime is immediately discoverable on the open web. A
merchant who deploys through Maritime gets NANDA registration as a side effect
with zero additional configuration.

**The joint opportunity: Firmly + LoginID as the trust layer on top of NANDA + Maritime**

This is the most underweighted opportunity in the prior analysis. Here is why
it matters:

NANDA + Maritime solves the discoverability problem: any buyer agent anywhere
can find any seller agent. But discoverability without trust is a fraud surface.
The buyer agent that discovers a seller on NANDA has no way to know if that
seller is legitimate, solvent, and accountable.

**Firmly's play:** Firmly Connect should offer a verified merchant tier on NANDA.
When a merchant onboards to Firmly Connect, Firmly registers their agent on
NANDA and co-signs the AgentFacts document with Firmly's key. A buyer agent
searching NANDA sees two tiers: unverified listings (self-asserted) and
Firmly-verified listings (co-signed by a known commerce infrastructure provider).
Buyer agent developers will filter to Firmly-verified by default, the same way
developers filter API marketplaces by "verified publisher." This makes Firmly
Connect the trust anchor for the entire NANDA discovery layer -- not just for
merchants who deploy through Firmly, but for buyer agents everywhere that want
to transact safely.

The Maritime integration makes this zero-friction: merchant signs up for Firmly
Connect, Firmly deploys their agent to Maritime, Maritime provides the HTTPS
endpoint, Firmly co-signs the NANDA AgentFacts. The merchant did nothing except
fill out the Firmly Connect onboarding form. This directly addresses the adoption
friction problem: no code, no DNS configuration, no separate NANDA registration,
no Maritime account. One form, fully deployed, verified, discoverable.

**LoginID's play on NANDA:** LoginID co-signs the AgentFacts document at the
human authorization layer. Where Firmly's signature says "this seller is a
verified Firmly Connect merchant," LoginID's signature says "the human who
registered this merchant was verified by FIDO2 biometric at registration time."
Two co-signatures on a single AgentFacts document: commerce infrastructure
trust (Firmly) plus human identity trust (LoginID). Together they answer both
questions a buyer agent needs: is this a legitimate seller? and did a real,
verified human register and authorize this agent?

**Why this creates a two-company moat:**

Neither Firmly nor LoginID can deliver both signatures alone. Firmly can verify
that a merchant has a working commerce integration, but cannot prove a human
authorized the deployment. LoginID can prove a human completed FIDO2 enrollment,
but cannot verify the merchant's commerce infrastructure is legitimate. Only the
joint co-signature delivers the complete trust signal. A buyer agent developer
who writes code to check for both signatures is now dependent on both companies
-- switching to a single-signature alternative means accepting a weaker trust
model.

**The Maritime deployment path as a product, not just infrastructure:**

Maritime's $1/month price point is not the product. The product is: from a
merchant's perspective, "I deployed my agent to Maritime and now I am verified
and discoverable everywhere." If Firmly Connect's onboarding includes Maritime
deployment + NANDA registration + LoginID co-signature as one automated step,
Maritime becomes the delivery mechanism for a trust bundle that no other hosting
platform offers. Maritime's current value is convenience. The joint value is
trust-at-deployment.

**Concrete implementation in SupplyMind terms:**

The SupplyMind codebase already has the skeleton:
- [src/seller_agent/nanda_facts.py](src/seller_agent/nanda_facts.py): generates the AgentFacts W3C VC
- [src/identity/keys.py](src/identity/keys.py): signs documents with secp256k1
- Maritime deployment manifest: built in Phase 6

What is missing: a second signature field in the AgentFacts document for the
Firmly co-signer key and the LoginID attestation record. Adding two fields to
the AgentFacts schema and publishing the co-signer public keys is a one-sprint
implementation for either company. The infrastructure already exists.

**Roadmap recommendation:**

- Firmly: "Verified on Firmly" tier for NANDA, automated via Maritime deployment
  in the Firmly Connect onboarding flow. Zero merchant effort. Buyer agents
  filter to Firmly-verified sellers by default. This is Firmly's distribution
  moat on the open agentic web -- not just for merchants who know about Firmly,
  but for every buyer agent that searches NANDA.

- LoginID: co-sign the AgentFacts document with biometric attestation of the
  registrant. Not the agent's credential -- the human who registered the
  merchant. Positioning: "LoginID-registered sellers have a verified human owner
  on record." This is the same Non-Repudiation product from the merchant section,
  applied at discovery time rather than transaction time.

- Joint: define the "Firmly + LoginID Verified Seller" co-signature standard.
  Publish the public keys. Write the buyer-agent verification SDK (two function
  calls: verify_firmly_signature, verify_loginid_attestation). Make it trivial
  for any buyer agent developer to filter for trusted sellers. The standard
  becomes infrastructure; the infrastructure creates lock-in.

**Urgency note:** NANDA is experimental today, but it is the only open,
decentralized, W3C-VC-based agent registry. The window to establish the
trust standard before a dominant player does is open now. A closed directory
(a single company's curated agent list) will emerge if the open registry does
not develop a credible trust layer. Firmly and LoginID are better positioned
than any other pair of companies to be that trust layer.

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

## Phase 10: Seller Authorization Manifest

| Criterion | LoginID | Firmly |
|-----------|---------|--------|
| Differentiation | Very high | Very high |
| Gap addressed | HTTPS is gone -- nothing replaces the padlock in agentic commerce | No seller-side signed offer standard exists |
| Standard clarity | No standard yet -- novel spec | No standard yet -- novel spec |
| Joint leverage | Very high | Very high |
| Regulatory tailwind | High | High |
| Enterprise sales fit | Very high | Very high |

**The problem this solves:**

In browser commerce, HTTPS is the cryptographic attestation layer. The padlock in
the URL bar tells the human buyer: "this server is operated by the entity named in
the certificate, and the connection is encrypted." That signal is so trusted it is
invisible -- users do not think about it, they just rely on it.

Agentic commerce removes the browser. There is no URL bar, no padlock, no SSL
certificate visible to the human. When a human buys from within Claude, ChatGPT,
or a TikTok feed, the interface navigates to the seller on their behalf. The human
has none of their normal "does this look sketchy" heuristics available.

Two concrete use cases where this matters today -- before autonomous buyer agents
exist at scale:

1. **Chat-native commerce:** Human tells Claude "order 500 reams of paper." Claude
   finds a seller, presents a quote, completes the purchase without leaving the chat.
   The human needs to know: is this seller real, and is this price what their owner
   actually authorized?

2. **Social commerce (TikTok, Instagram):** Human sees a product in a feed, taps
   buy, purchase completes inside the app. Merchant owns the customer relationship,
   no redirect to a storefront. Same question: is this offer genuine and authorized?

In both cases the interface (Claude, TikTok) needs a machine-readable trust signal
it can verify and surface to the human: "this seller is verified." The same way
Uber shows a driver rating before you get in the car.

**What the Seller Authorization Manifest is:**

A signed document created by the merchant's human operator before the selling agent
goes live. It states: "this agent may sell these SKUs, at these price ranges, with
these discount limits." The selling agent signs each quote against this manifest.
The buyer agent -- or the chat interface acting on a human's behalf -- receives a
signed offer and can verify: the merchant's human owner authorized this product at
this price. Any deviation from the manifest (unauthorized SKU, price outside range,
discount exceeding limit) fails verification before the human is asked to confirm.

This is not AP2. AP2 is buyer-side governance by design -- it governs what a buyer
agent can spend, not what a seller agent can offer. The Seller Authorization
Manifest borrows AP2's cryptographic pattern (secp256k1-signed document, human
operator key, agent execution key) and applies it to the seller side. No standard
exists for this yet. It is a novel spec.

**LoginID:** The merchant operator signing ceremony. When a merchant's head of
e-commerce or ops manager creates the Seller Authorization Manifest in Firmly
Connect, LoginID handles the signing step -- Touch ID, Face ID, or hardware key.
The manifest becomes a hardware-attested artifact: this human, at this company,
authorized this agent to sell these products at these prices. This is LoginID's
most natural enterprise merchant product -- identical signing ceremony to the
Intent Mandate but on the seller side.

**Firmly:** Firmly Connect generates the Seller Authorization Manifest at merchant
onboarding -- zero additional merchant action required. The manifest is stored in
the Agent Control Center alongside the seller's DNSid registration. Buyer agents
(and chat interfaces) can fetch and verify it via a standard endpoint. Firmly
becomes the trust infrastructure that makes a seller verifiable without a browser.
This is also a direct response to the Shopify question: Shopify merchants have
HTTPS but no Seller Authorization Manifest. Firmly-connected merchants have both.

**Joint:** LoginID signs the manifest (human attestation); Firmly generates,
stores, and serves it (merchant infrastructure). The chat interface or social
platform fetches the manifest from Firmly's endpoint, verifies the LoginID
signature, and surfaces "verified seller" to the human buyer. Neither company
can deliver the complete signal alone.

**Clerk's Four Auth Questions -- Phase 10 contribution:**

Phases 7 through 9 advanced Identity, Scoping, and Approvals on the buyer side.
Phase 10 is the first phase that meaningfully advances Enforcement on the seller
side -- and Enforcement has been the weakest layer throughout.

- **Identity:** seller DNSid (Phase 8) establishes who the agent is. Phase 10
  adds: the human owner is cryptographically bound to the agent's authorization.
- **Scoping:** the Seller Authorization Manifest defines exactly what the agent
  is permitted to sell, at what prices, with what discount limits. This is
  seller-side scoping -- the buyer-side equivalent is the Intent Mandate (Phase 9).
- **Approvals:** the manifest is signed by the merchant operator (LoginID ceremony).
  Each signed quote is the agent's approval artifact for that specific offer.
- **Enforcement (the key advance):** without the manifest, a compromised or rogue
  seller agent can quote any price, any SKU, any discount -- and the buyer has no
  way to detect deviation at transaction time. With the manifest, the chat interface
  or buyer agent verifies the quote against the signed baseline before presenting
  it to the human. Deviation fails at the transaction boundary, not in an audit
  log after money has moved. This is runtime enforcement, not retrospective
  detection -- the first instance of that in the SupplyMind architecture.

**Roadmap recommendation:** Build alongside Phase 9 (AP2 v0.2.0) as the seller-side
complement. Propose as a companion standard to AP2 -- Firmly leads the spec,
LoginID leads the signing ceremony. The reference implementation in SupplyMind
is the proof of concept for both companies.

**Merchant friction analysis and deployment strategy:**

Firmly's customer is the merchant, and merchants resist complex implementations.
Phase 10 has three friction points that must be addressed before broad adoption:

1. The signing ceremony (low friction -- one biometric gesture at onboarding,
   LoginID designed for this).
2. Defining price ranges and discount limits (medium friction -- requires the
   merchant to think explicitly about pricing policy, potentially involving a
   different team than whoever implements Firmly).
3. Re-signing when prices change (high friction if frequent -- kills adoption
   for merchants with dynamic pricing or frequent promotions).

The key insight: **the merchant already approved these prices when they loaded
them into their existing system.** The manifest does not need a new approval
process -- it needs to read the approval that already happened and sign it.

Three approaches in order of merchant friction, lowest to highest capability:

**Approach 1: Price buffer policy (no-code, zero ongoing friction) -- launch here**
Merchant sets one policy at onboarding: "authorize my agent to sell anything in
my catalog at plus or minus X% of listed price, with a maximum discount of Y%."
Firmly applies that policy globally. The manifest auto-regenerates on every
catalog sync. The merchant never touches it again unless the policy changes.
Re-signing is only required when the policy itself changes, not when individual
prices change. This is the true no-code path and the right launch configuration.

**Approach 2: Catalog-sync manifest (low friction, SKU-level control) -- mid-market**
Firmly reads the merchant's existing catalog (UCP feed, Shopify product API, or
any feed already exposed). Auto-generates the manifest with price ranges derived
from current prices plus the configured buffer. Merchant sees a one-screen summary:
"Your agent is authorized to sell these 47 SKUs at these ranges. Confirm with
Face ID." One tap. Re-signing triggers automatically as a mobile push notification
when catalog changes exceed the buffer threshold. The merchant never needs to
understand what a manifest is.

**Approach 3: ERP and PIM agent integration (enterprise tier) -- highest value**
An MCP server connects to the merchant's ERP (SAP, NetSuite, Dynamics) or PIM
(Akeneo, Salsify). An agent reads approved prices, active SKUs, and existing
discount rules directly from the merchant's internal source of truth. The manifest
is constructed automatically from data the merchant's pricing team already approved.
The LoginID signing ceremony is the final step: biometric confirmation that "yes,
this reflects what our system already says." Zero manual data entry. Re-signing
triggers when the ERP data changes beyond threshold.

This is the strongest LoginID differentiation: the signing is tied to a specific
named person reviewing a manifest derived from a live enterprise system, with
hardware attestation that they were present at that moment. Gmail cannot produce
this artifact. An auditor or dispute resolution process can verify exactly who
approved what pricing policy, when, from which system of record.

**Implementation note for SupplyMind:** Approach 3 is a natural Phase 17 or 18
addition -- an MCP server that reads from a mock ERP and feeds the manifest
creation flow. This would be the first end-to-end demonstration of the
LoginID + Firmly + ERP integration that neither company has built yet.

---

## Phase 11: Governance Dashboard

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

**What was built in SupplyMind:**
The governance dashboard (port 8085) answers all four Clerk questions via HTTP
endpoints. A durable audit log (`logs/audit.jsonl`) records every event as it
happens -- agent registrations, manifest signings, mandate creation, transaction
completions. The log persists across server restarts. Every event includes
timestamp, layer, event type, entity, operator, and detail. A CISO can open
the file directly or query it via `GET /governance/audit-trail`.

The dashboard reads live data from the seller server via HTTP (cross-process safe).
This is the architecture Firmly would use in production: a separate read-only
audit service reading from the operational service, not sharing its memory.

---

## Phase 12: Multi-Protocol Checkout (ACP + UCP)

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

## Phase 13: Agent Wallet Layer

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

## Phase 14: Network Credential Layer (Visa TAP + Mastercard Agent Pay)

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

## Phase 15: Fraud and Bot Detection

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

## Phase 16: Stablecoin Settlement (x402 + AWS AgentCore)

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

Both companies sell to the same customer: the merchant. The joint product at each
layer gives the merchant something neither company can deliver alone.

| Layer | LoginID contribution | Firmly contribution | What the merchant gets |
|-------|---------------------|--------------------|-----------------------|
| Agent discovery | Co-signs AgentFacts with human attestation of registrant | Co-signs AgentFacts as verified commerce partner; deploys via Maritime | Discoverable on NANDA with two-company trust seal -- neither signature alone is sufficient |
| Spending governance | Biometric authorization ceremony for mandate creation | ACF tiers + AP2 mandate engine + Agent Control Center UI | A mandate that is legally defensible in a dispute and auditable by a regulator |
| Dispute protection | Non-Repudiation record: signed proof of who authorized the mandate | Transaction record linking mandate to order | Complete chain from human biometric to executed transaction |
| Compliance audit trail | Human attestation log with hardware credential metadata | Mandate ledger + full Clerk 4-question coverage | CISO-grade artifact for annual audit or regulatory examination |
| Network credentials | Biometric consent ceremony for Visa TAP / MC Agent Pay enrollment | Validates network credentials before accepting any agent purchase | Bank-grade agent authorization with human biometric provenance |
| Fraud detection | Credential legitimacy score (hardware vs. software vs. none) | Traffic classifier fed by all Firmly Connect merchant data | Two independent signals converging on the same anomaly |

---

## Firmly Distribution Strategy: Three-Path Partnership Model

### The Core Problem

Merchants need their selling agents to be discoverable by buyer agents. No universal
standard exists yet. NANDA is the most credible open candidate, but betting only on
NANDA adoption is strategically risky. The three-path model hedges across ecosystem
maturity so Firmly builds compounding distribution regardless of which standard wins.

---

### Path 1: NANDA + Maritime (Available Now)

Firmly and LoginID co-sign AgentFacts documents as a two-company trust seal.
Maritime.sh delivers it zero-friction: one merchant form gets HTTPS endpoint,
NANDA registration, and co-signed identity in a single workflow.

**Risk:** Depends on NANDA becoming the open standard. If closed directories
(Shopify, Amazon, Google Shopping) capture the market instead, NANDA adoption
stalls and this path loses leverage.

**Window:** Mid-2026 is early enough to establish the co-signature as the trust
standard before a closed directory fills the gap. This window closes as the larger
platforms ship their own agent discovery products.

---

### Path 2: Agent Builder SDK and Platform Partnerships

Embed Firmly's commerce infrastructure in the tools developers use to build agents.
If Firmly is part of the construction layer, merchants and buyers get Firmly by
default without a separate integration decision.

**Two distinct partnership mechanics:**

**Seller-side builder platforms** (where merchants build their selling agents):
Firmly becomes the default checkout and catalog protocol layer. Merchant deploys
a selling agent pre-wired to accept any buyer agent. This is the most direct
extension of Firmly's existing motion.

**Buyer-side builder platforms** (where enterprises build procurement agents):
Firmly becomes the payment and vendor discovery layer those agents already speak.
Merchants who want inbound traffic from Firmly-connected buyer agents connect
to Firmly -- a demand-generation pull rather than a direct sale.

**Candidate partners (research status -- requires verification before outreach):**

| Platform | Side | Commerce angle | Est. size | Notes |
|---|---|---|---|---|
| **CrewAI** | Buyer | Multi-agent B2B enterprise workflows; procurement and ops agents | Series A range | Founder-accessible; explicitly targets enterprise use cases where procurement agents live |
| **LangChain / LangGraph** | Both | Most widely used agent orchestration framework; LangGraph becoming standard for multi-agent | Series B range | Very large developer install base; commerce angle indirect; may be harder to partner with commercially than size suggests -- needs verification |
| **Composio** | Buyer | Tool integration platform for agents (Zapier for AI agents); commerce tools already integrated | Early stage | Sits between agent and tool -- exactly where Firmly's protocol abstraction lives; strong technical fit |
| **Relevance AI** | Both | No-code agent builder; explicit B2B workflow focus | Series A range | Targets business users not just developers; aligns with Firmly's no-code merchant positioning; low partnership friction |
| **Beam AI** | Buyer | Agentic process automation; enterprise procurement focus | Early stage | High persona fit (their buyer = Firmly's buyer); worth direct founder outreach |
| **AgentKit (Coinbase)** | Buyer | Agent framework with native wallet and payment primitives; x402 alignment | Coinbase-backed | Commerce-adjacent but crypto-native; B2B procurement persona not primary; lower fit than others |
| **AutoGen (Microsoft)** | Both | Microsoft-backed multi-agent framework; enterprise credibility | Microsoft org | Enterprise distribution is attractive; Microsoft relationship dynamics make commercial partnership difficult; monitor rather than pursue |

**Note:** Size estimates above are approximate and require verification. Do not
filter candidates based on size assumptions -- a "large" framework may still be
an accessible partnership if Firmly approaches the right team.

**Recommended starting point:** CrewAI and Relevance AI. Both are founder-accessible,
both have explicit enterprise/B2B commerce angles, and both serve the merchant
persona Firmly already sells to.

---

### Path 3: Foundation Model Partnerships (Long Term)

Anthropic, Google (Gemini), OpenAI. If Firmly is the native commerce infrastructure
for Claude or Gemini agents, distribution is transformative -- any agent on those
platforms buying or selling would run through Firmly.

**Why this is not today's move:** Firmly needs meaningful merchant volume and
transaction data before foundation model providers have a commercial reason to
prefer Firmly over building their own commerce layer. The leverage point is
proving that Firmly-connected merchants convert better, have lower dispute rates,
and produce better agent commerce outcomes than unconnected merchants.

**Trigger:** When Firmly has 500+ live merchants and measurable transaction data,
revisit Anthropic and Google partnerships. LoginID's relationships with enterprise
buyers (their existing B2B customers) may provide warm intros to the right teams
at foundation model companies.

---

### Shopify: Competitor or Partner?

**Firmly's current position:** Firmly serves non-Shopify merchants -- the enterprises
and mid-market B2B sellers that do not run on Shopify's platform. From this lens,
Shopify is a parallel track: they will build their own agentic commerce story for
their own merchant base, and Firmly builds the infrastructure for everyone else.

**The case for reconsidering this:**

Shopify is not a monolithic competitor. They are a platform with an app ecosystem.
The relevant question is not "Shopify vs. Firmly" but "does Shopify's agentic
commerce product serve the needs of enterprise B2B merchants the way Firmly does?"

Three reasons to challenge the competitor framing:

1. **Shopify's core strength is B2C, not B2B.** Shopify Commerce is optimized for
   consumer checkout -- high volume, low SKU complexity, card-on-file payments.
   Enterprise B2B procurement (the market Firmly serves) has different requirements:
   AP2 mandates, multi-party approval workflows, contract pricing, net-30 terms,
   compliance audit trails. Shopify does not natively solve these. Firmly does.
   This means there is a real gap even inside the Shopify merchant base -- Shopify
   merchants who want to accept B2B agent purchases may need Firmly's layer on top.

2. **Shopify's app ecosystem is a distribution channel, not a competitor.**
   A "Firmly Connect for Shopify" app would let Shopify merchants accept AP2-governed
   agent purchases, handle x402 micro-payment challenges, and surface in NANDA
   with a co-signed AgentFacts document -- none of which Shopify builds natively.
   Shopify benefits (their merchants can accept a new class of buyers); Firmly
   benefits (access to Shopify's merchant distribution without a direct sales motion).
   This is a Path 2 partnership, not a competitive battle.

3. **The agentic commerce layer sits above the e-commerce platform layer.**
   A buyer agent does not care whether the seller runs on Shopify, Magento, or a
   custom ERP. It cares whether the seller speaks AP2, UCP, and A2A. Firmly's value
   is in the protocol abstraction layer above the commerce platform -- which means
   Firmly can ride Shopify's distribution rather than fight it.

**Recommended framing for Firmly:** Shopify is the largest distribution channel
for Path 2, not a competitor. The question to ask Firmly: "Are there Shopify
merchants who want to sell to enterprise buyer agents and cannot do it natively
through Shopify?" If yes, a Firmly app in the Shopify App Store reaches those
merchants with zero Firmly sales effort.

**What needs verification:** How Shopify is currently building their own agentic
commerce features (they have announced Sidekick and related AI products). If
Shopify ships native AP2 and A2A support, the gap narrows. If they build a
proprietary checkout flow for agents, Firmly's open-protocol positioning becomes
a stronger differentiator for merchants who need interoperability.

**Action item:** Understand Shopify's agentic commerce roadmap before finalizing
the competitor vs. partner framing. This will be naturally illuminated during
Phase 11 (Multi-Protocol Checkout), where ACP and UCP checkout flows are built
and Shopify's approach to these protocols becomes directly relevant.

---

## Priority Matrix

Priorities reflect: merchant willingness to pay today, joint leverage (neither
alone delivers it), and the window before a competitor occupies the position.

| Priority | Initiative | Owner | Phase | Rationale |
|----------|-----------|-------|-------|-----------|
| 1 | "Firmly + LoginID Verified Seller" co-signature on NANDA | Jointly | 6 | Establishes trust standard on the open agentic web before a closed directory does; Maritime makes it zero-friction for merchants; buyer agents have a strong reason to prefer verified sellers |
| 2 | Human Attestation for Agent Mandates | Jointly | 4, 9 | Mandate becomes legally defensible; shared customer (merchant); clearest dollar ROI |
| 3 | CISO-grade enterprise governance dashboard | Firmly | 10 | Most valuable single product for enterprise sales motion; LoginID feeds attestation data |
| 4 | Visa TAP + Mastercard Agent Pay integration | Both | 13 | Highest regulatory urgency; financial services segment |
| 5 | Non-Repudiation as a Service | LoginID | 4, 9 | Dispute protection product; direct dollar ROI for high-value merchant transactions |
| 6 | Compliance Attestation Certificate | LoginID | 10 | Regulated industry segment; annual subscription model |
| 7 | Hardware-backed agent key management ("FIDO2 for agents") | LoginID | 7 | Strong differentiation; no competitor has hardware-bound agent keys |
| 8 | Agent wallet KYC binding | LoginID | 12 | Regulatory requirement incoming; ahead of mandate |
| 9 | Agent Velocity Monitoring (anomaly signal) | LoginID | 14 | Fraud signal only LoginID can compute; feeds Firmly classifier |
| 10 | Catalog document signing | Firmly | 2 | Real gap; Firmly's position enables it; lower urgency than discovery layer |
| 11 | x402 / stablecoin settlement | Both | 15 | Monitor; revisit when x402 moves to maturing |

---

## The Single Framing Sentence

LoginID and Firmly are the trust layer for the open agentic web. Firmly verifies
the merchant's commerce infrastructure; LoginID verifies the human who controls
it. Together their co-signature on a NANDA AgentFacts document -- deliverable
today via Maritime with zero merchant effort -- is the only signal that tells
a buyer agent both "this seller is a legitimate commerce partner" and "a verified
human is accountable for this agent." No single company can produce both halves.
That is the enterprise wedge and the network moat.

The deeper insight from Clerk's analysis: enforcement is the weakest layer across
the entire agentic commerce industry in mid-2026. Every current system handles
identity and approvals reasonably well, but no production system fully prevents
a compromised agent from bypassing its own policy. The joint LoginID + Firmly
product -- biometric-attested mandate, cryptographically signed, surfaced in a
CISO dashboard -- is the closest thing currently achievable to a real enforcement
engine. Not because it solves the runtime enforcement problem (no one has),
but because it creates the audit trail that makes non-compliance provable after
the fact. In regulated industries, that is sufficient for purchasing decisions.
