"""
Database layer for the Inventory MCP Server.

Protocol context: No protocol runs here. This module is purely SQLite (stdlib).
It is called by server.py at startup so the MCP server always has a live DB.

wallet_address: Each product row stores a Circle Programmable Wallet address.
This is a public receive-only identifier — safe to expose in API responses.
Phase 4 (AP2/MPP) will read it to route USDC settlement to the correct seller wallet.
"""

import sqlite3
import hashlib
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "inventory.db"

PRODUCTS = [
    # ACF tier: AUTO (under $5) — agent pays immediately, no notification
    ("STG-002", "Binder Clips (Box of 100)",       "stationery",  "Assorted sizes: small, medium, large",                              1.99, 600, "box"),
    ("DSK-002", "Whiteboard Markers (Set of 8)",   "desk",        "Dry-erase, chisel tip, assorted colors, with eraser",               3.49, 300, "set"),
    ("DSK-003", "Tape Dispenser + 6 Rolls",        "desk",        "Heavy-duty dispenser with 6 rolls of 3/4in clear tape",             4.99, 200, "set"),
    # ACF tier: NOTIFY ($5 to $10) — agent pays but logs human notification
    ("PEN-001", "Ballpoint Pens (Box of 50)",      "pens",        "Medium point blue ink, retractable",                                5.99, 500, "box"),
    ("PPR-002", "Legal Pads (12-pack)",            "paper",       "Yellow ruled legal pads, 8.5x14, 50 sheets each",                   6.49, 150, "pack"),
    ("STG-001", "Staples (5000-count box)",        "stationery",  "Standard 26/6 staples for desktop staplers",                        7.99, 400, "box"),
    ("DSK-001", "Desk Organizer Set",              "desk",        "5-piece set: pen cup, paper tray, file sorter, clip dish, drawer",  8.99,  80, "each"),
    ("PPR-003", "Sticky Notes (24-pack)",          "paper",       "3x3 inch repositionable notes, assorted colors",                    9.49, 300, "pack"),
    # ACF tier: BLOCK (over $10) — agent stops, requires human approval
    ("PEN-002", "Fine-tip Markers (Box of 24)",    "pens",        "Permanent ink, fine point, assorted colors",                       10.99, 200, "box"),
    ("PEN-003", "Highlighters (Box of 36)",        "pens",        "Chisel tip, assorted fluorescent colors",                          11.49, 180, "box"),
    ("STG-003", "Manila Folders (Box of 100)",     "stationery",  "Letter size, 1/3 cut tabs, kraft manila",                          12.99, 250, "box"),
    ("STG-004", "3-Ring Binders 1in (Box of 12)", "stationery",  "1-inch D-ring binders, assorted colors",                           13.99, 100, "box"),
    ("PPR-001", "Copy Paper (Case, 10 reams)",     "paper",       "Standard 8.5x11 copy paper, 20lb bond, 500 sheets/ream",           14.99, 200, "case"),
    ("TNR-002", "Inkjet Cartridge Set (CMYK)",     "toner",       "Cyan, Magenta, Yellow, Black ink set for Epson WorkForce",          18.99, 120, "set"),
    ("TNR-001", "Laser Toner Cartridge (Black)",   "toner",       "High-yield black toner, compatible with HP LaserJet series",        24.99,  75, "each"),
]


def _wallet_for_sku(sku: str) -> str:
    """
    Generate a deterministic simulated Circle wallet address from a SKU.
    In production this would be a real Circle Programmable Wallet address
    retrieved from the Circle API at onboarding time.
    """
    digest = hashlib.sha256(sku.encode()).hexdigest()[:40]
    return f"0x{digest}"


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            sku             TEXT UNIQUE NOT NULL,
            name            TEXT NOT NULL,
            category        TEXT NOT NULL,
            description     TEXT,
            unit_price      REAL NOT NULL,
            stock_qty       INTEGER NOT NULL,
            unit_of_measure TEXT NOT NULL DEFAULT 'each',
            wallet_address  TEXT NOT NULL
        )
    """)

    cur.executemany(
        """
        INSERT OR IGNORE INTO products
            (sku, name, category, description, unit_price, stock_qty, unit_of_measure, wallet_address)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [(*row, _wallet_for_sku(row[0])) for row in PRODUCTS],
    )

    conn.commit()
    conn.close()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def reset_db() -> None:
    """Drop and recreate the products table, then re-seed with current PRODUCTS list."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS products")
    conn.commit()
    conn.close()
    init_db()


if __name__ == "__main__":
    import sys
    if "--reset" in sys.argv:
        reset_db()
        print("Database reset and re-seeded with new prices.")
    else:
        init_db()
    conn = get_connection()
    rows = conn.execute(
        "SELECT sku, name, unit_price, stock_qty, wallet_address FROM products ORDER BY unit_price"
    ).fetchall()
    conn.close()
    print(f"{'SKU':<10} {'Name':<38} {'Price':>8} {'Stock':>6}  ACF Tier")
    print("-" * 90)
    for r in rows:
        p = r["unit_price"]
        tier = "AUTO  (<$5)" if p < 5 else ("NOTIFY ($5-$10)" if p <= 10 else "BLOCK  (>$10)")
        print(f"{r['sku']:<10} {r['name']:<38} ${p:>7.2f} {r['stock_qty']:>6}  {tier}")
