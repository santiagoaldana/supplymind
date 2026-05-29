# SupplyMind — CLAUDE.md

## Project Purpose

SupplyMind is a hands-on learning project to deeply understand how AI agents buy, sell, and transact — by building a working multi-agent B2B commerce system from scratch. It is also a portfolio artifact for Santiago Aldana's executive job search in Agentic AI / payments / BaaS.

**Owner:** Santiago Aldana — MIT Sloan MBA, 20+ yrs FinTech/AI/payments/LATAM leadership.

**Dual purpose:**
1. Technical depth: build real, working implementations of MCP, A2A, UCP, and Agentic Payments protocols.
2. Job search signal: every milestone becomes a LinkedIn post, outreach hook, or talking point. Insights go into `../SHARED_CONTEXT.md`.

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
  README.md                        # Project overview
  requirements.txt
  .env                             # API keys (never commit)
  agentic-commerce-learning-plan.pdf
  src/
    inventory_server/              # Phase 1: MCP server, SQLite-backed
    shipping_server/               # Phase 1: MCP server, stub responses
    payment_server/                # Phase 4: MCP server, spending guardrails
    buyer_agent/                   # Phase 3+: Claude as buyer, A2A client
    seller_agent/                  # Phase 3+: FastAPI + Claude, A2A server
  data/                            # SQLite DBs, seed data
  logs/                            # Tool call traces, run logs
  tests/                           # Phase test scripts
```

## 5-Phase Build Plan

| Phase | Focus | Protocols | Est. Time |
|-------|-------|-----------|-----------|
| 1 | MCP servers (inventory + shipping) + Claude as client | MCP | 2-3 days |
| 2 | UCP-compliant product catalog + quote objects | UCP + MCP | 2-3 days |
| 3 | A2A agent cards, task lifecycle, buyer/seller discovery | A2A + UCP + MCP | 3-4 days |
| 4 | Agentic Payment MCP server, spending guardrails | API + A2A + MCP | 3-4 days |
| 5 | Full demo, second seller, dashboard, protocol reflection doc | All | 2-3 days |

**Current phase:** Phase 1

## Key Protocols

- **MCP (Model Context Protocol):** Anthropic standard. Tools, resources, prompts. stdio or SSE transport.
- **A2A (Agent-to-Agent):** Google DeepMind. Agent Cards (agent.json), task lifecycle (POST /tasks/send, GET /tasks/{id}).
- **UCP (Universal Commerce Protocol):** Semantic layer for machine-readable product catalogs, pricing tiers, quote objects.
- **Agentic Payment Interface:** AI agents autonomously initiate/authorize payments with human-set guardrails.

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

## Shared Context

The file `../SHARED_CONTEXT.md` is the bridge between this project and the Job Search project. The Job Search Claude session reads from it to draft LinkedIn posts and outreach hooks.

**When Santiago says "update shared context"**, append a new entry to the Milestone Log section of `../SHARED_CONTEXT.md` using this format:

```
### <Phase or topic> — <one-line description>
**Date:** <today's date>
**Built:** <what was implemented>
**Surprising:** <what was non-obvious or counter-intuitive>
**Quotable:** <one punchy sentence ready to use in a LinkedIn post or outreach>
```

Do not rewrite existing entries. Only append. Keep quotables first-person and concrete ("I learned that..." or "Building X revealed..."). No em dashes in any copy.

## Models

- `claude-opus-4-6` for agent reasoning tasks
- `claude-haiku-4-5-20251001` for classification or lightweight tool calls
