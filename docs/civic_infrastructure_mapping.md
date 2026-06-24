# Civic Agent Infrastructure: RFC Mapping to SupplyMind

Status: working note for further discussion. Captured 2026-06-24.

## Source

RFC concept paper: "Public Infrastructure for Private Agents: An AI Framework
for Every Massachusetts Resident."

Authors: Santiago Garces (Chief Information Officer, City of Boston), Gabriela
Torres (MassTech AI Innovation Ecosystem Development), Ashish Bhatia (Product),
Ramesh Raskar (MIT, founding architect of ProjectNANDA).

Short URL: http://tiny.cc/agents4ma. Comments to OET@boston.gov.

Shared lineage matters: the paper builds on NANDA architecture and Raskar's MIT
team, the same protocol family SupplyMind is built on. The parallels below are
not coincidental.

## What the RFC argues

AI agents will mediate how residents interact with government. The paper does
not propose a government run agent for every citizen. It proposes a public
infrastructure layer: open protocols and interfaces that let any agent (built
by Anthropic, Google, a startup, or a neighborhood org) interact with civic
services in an authenticated, privacy preserving way, with guaranteed access
regardless of ability to pay for a private subscription.

Framing from Boston's CIO: the right to access civic services through an AI
agent without corporate capture of your data. Government as rule setter and
infrastructure provider, not monopolist or product.

Three risks the paper names: data capture (civic data becomes proprietary
training data), walled gardens (forced choice between civic access and platform
loyalty), and equity inversion (free agents monetize data while paid ones
protect privacy, so the poorest are most exposed). Privacy framed as a right,
not a luxury, with government using procurement power to buy privacy for low
income residents. UPI in India is the recurring model: public protocol, public
reference implementation, private players build on top, no one owns the rails.

By its own admission the paper has not built any of this. It calls for four
working groups over twelve months: Identity and Authentication, Civic Services
Interface, Equity and Privacy and Digital Access, Governance and Policy.

## The core mapping

The RFC's four layer agent ecosystem is the same structure SupplyMind already
implements, with different actors. SupplyMind has running code for Layers 1 to
3; the RFC is still at concept stage for all of it.

| RFC Layer | RFC actor | SupplyMind equivalent |
|---|---|---|
| L1 Government/City agents | Boston Open Context MCP server | inventory / shipping / payment MCP servers (Phase 1, 4) |
| L2 Business agents, KYA certified | MBTA, hospitals | Seller Agent with Seller Authorization Manifest (Phase 10) and KYA signing (Phase 6) |
| L3 Resident agents, delegated and portable | Personal citizen agents | Buyer Agent acting on delegated AP2 mandates (Phase 4, 9) |
| L4 Unregulated | Red Sox agent | Out of scope for both |

Headline: SupplyMind is a running proof of concept for the exact stack this RFC
says needs to be built.

## Concept by concept

1. Know Your Agent (KYA). The RFC's central unsolved governance problem (WG4;
   Dr. Elijah Miller's comment frames it as legal addressability, no
   consequential action comes from no one). SupplyMind implements KYA signing
   (Phase 6, secp256k1, DID) and the Seller Authorization Manifest (Phase 10).
   The protocol_reflection.md security analysis against Clerk's four auth
   questions (Identity, Scoping, Approvals, Enforcement) is the framework WG4 is
   asking someone to produce.

2. Identity as 80 percent of the solution. The RFC's claim is OAuth plus
   verified email plus delegated acts. SupplyMind goes further with DNSid
   ownership anchoring (Phase 8) and cryptographic identity (Phase 6). Open RFC
   question (independent agent identity vs delegated access) can be answered
   empirically from SupplyMind: AP2 mandates are delegated scoped credentials,
   DNSid gives the agent an independent anchored identity. Both built; tradeoff
   can be spoken to from code.

3. MCP as the governed interface / minimal privacy surface. The RFC insight
   (the server sees which tool was called and what returned, not user intent) is
   exactly the SupplyMind MCP server design plus the logs/audit.jsonl append
   only trace, which is the enforcement and observability layer WG4 wants.

4. Probabilistic into deterministic (WG2). The hardest open RFC question, also
   flagged by commenters Siran Cao and Nathan Storey: how does a non
   deterministic agent safely write into deterministic government systems? This
   is the AP2 procurement loop (Phase 4) plus tiered autonomy (ACF) plus Human
   Not Present logic (Phase 9). The mandate engine with human confirmation
   thresholds is one concrete answer.

5. UPI analogy. The RFC leans on UPI (public rails, no owner). SupplyMind's
   Phase 16 reasoning on AP4M (replicate Mastercard's closed network as an open
   permissionless protocol via x402 plus Base) is the same argument applied to
   payments.

## Gap the RFC has that SupplyMind does not

Nathan Storey's comment proposes an output provenance / verification layer:
attest to the analysis an agent produced and how (method, inputs, corroborating
signals), not just who it acts for. An open signed provenance format the civic
interface could require at submission. SupplyMind attests identity and
authorization (who, what scope) but not the reasoning or output of a
transaction. Genuine gap in the SupplyMind stack.

## Candidate next moves

1. Keep this mapping as the basis for positioning SupplyMind as a transferable
   reference implementation for civic agent infrastructure.
2. Phase 18 candidate: output provenance / signed determination layer. Signed
   attestation of what an agent decided and how, extending the existing
   secp256k1 identity layer. This is the one thing RFC commenters want that
   SupplyMind currently lacks.

## Open threads for discussion

- Whether to write a public facing version of this mapping (the MBA / portfolio
  framing: built the working prototype of the thing Boston's CIO is writing an
  RFC about).
- Whether to apply to a working group, and which (WG1 Identity and WG4
  Governance are the closest fit to existing SupplyMind work).
- Scope and design of the Phase 18 provenance layer.
