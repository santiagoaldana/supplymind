"""
Phase 5B: Live Terminal Dashboard

Displays a real-time view of the procurement run using Rich Live.
Updated after each key event: discovery, selection, payment decision, settlement.

Usage:
    dashboard = Dashboard()
    with dashboard.live():
        dashboard.set_sellers(["Seller A", "Seller B"])
        dashboard.add_event("DSK-002", "AUTO", "EXECUTED", 3.49)
        ...
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box


@dataclass
class PaymentEvent:
    sku:        str
    name:       str
    seller:     str
    amount:     float
    acf_tier:   str
    outcome:    str
    fiat_ref:   str = "N/A"
    usdc_ref:   str = "N/A"
    timestamp:  str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%H:%M:%S"))


class Dashboard:
    def __init__(self) -> None:
        self._sellers:  list[dict]         = []
        self._events:   list[PaymentEvent] = []
        self._mandate:  dict               = {}
        self._status:   str                = "Initializing..."
        self._live:     Optional[Live]     = None
        self._console   = Console()

    def live(self) -> Live:
        self._live = Live(
            self._render(),
            console=self._console,
            refresh_per_second=4,
            screen=False,
        )
        return self._live

    def _refresh(self) -> None:
        if self._live:
            self._live.update(self._render())

    def set_status(self, msg: str) -> None:
        self._status = msg
        self._refresh()

    def set_sellers(self, sellers: list[dict]) -> None:
        self._sellers = sellers
        self._refresh()

    def set_mandate(self, mandate: dict) -> None:
        self._mandate = mandate
        self._refresh()

    def add_event(self, event: PaymentEvent) -> None:
        self._events.append(event)
        if self._mandate and event.outcome == "EXECUTED":
            self._mandate["spent_total_usd"] = round(
                self._mandate.get("spent_total_usd", 0) + event.amount, 2
            )
            self._mandate["tx_count"] = self._mandate.get("tx_count", 0) + 1
        self._refresh()

    def _render(self) -> Panel:
        layout = Layout()
        layout.split_column(
            Layout(name="status",   size=3),
            Layout(name="sellers",  size=7),
            Layout(name="mandate",  size=6),
            Layout(name="events"),
        )

        # Status bar
        layout["status"].update(Panel(
            f"[bold cyan]{self._status}[/bold cyan]",
            title="SupplyMind Phase 5B — Multi-Seller Live Dashboard",
            border_style="blue",
        ))

        # Sellers table
        s_table = Table(box=box.SIMPLE, show_header=True, expand=True)
        s_table.add_column("Seller",     style="cyan")
        s_table.add_column("DID",        style="dim")
        s_table.add_column("Port",       justify="right")
        s_table.add_column("Status",     justify="center")
        for s in self._sellers:
            status_color = "green" if s.get("ready") else "yellow"
            status_label = "READY" if s.get("ready") else "starting..."
            s_table.add_row(
                s.get("name", ""),
                s.get("did", ""),
                str(s.get("port", "")),
                f"[{status_color}]{status_label}[/{status_color}]",
            )
        layout["sellers"].update(Panel(s_table, title="Sellers", border_style="cyan"))

        # Mandate panel
        if self._mandate:
            spent     = self._mandate.get("spent_total_usd", 0)
            total     = self._mandate.get("max_total_usd", 0)
            remaining = round(total - spent, 2)
            pct       = int((spent / total * 100)) if total else 0
            bar_filled = int(pct / 5)
            bar = "[green]" + "█" * bar_filled + "[/green]" + "░" * (20 - bar_filled)
            mandate_text = (
                f"ID         : [cyan]{self._mandate.get('mandate_id', '')[:16]}...[/cyan]\n"
                f"Spent      : [green]${spent:.2f}[/green] / [dim]${total:.2f}[/dim]  {bar}  {pct}%\n"
                f"Remaining  : [green]${remaining:.2f}[/green]   "
                f"Transactions: [green]{self._mandate.get('tx_count', 0)}[/green]"
            )
        else:
            mandate_text = "[dim]Mandate not yet created[/dim]"
        layout["mandate"].update(Panel(mandate_text, title="AP2 Mandate", border_style="green"))

        # Events table
        e_table = Table(box=box.SIMPLE, show_header=True, expand=True)
        e_table.add_column("Time",    style="dim",   width=9)
        e_table.add_column("SKU",     style="cyan",  width=9)
        e_table.add_column("Seller",  width=16)
        e_table.add_column("Amount",  justify="right", width=8)
        e_table.add_column("ACF",     justify="center", width=8)
        e_table.add_column("Outcome", justify="center", width=10)
        e_table.add_column("Stripe Ref", style="dim")

        for ev in self._events[-12:]:  # show last 12
            tier_color    = {"AUTO": "green", "NOTIFY": "yellow", "BLOCK": "red"}.get(ev.acf_tier, "white")
            outcome_color = "green" if ev.outcome == "EXECUTED" else "red"
            e_table.add_row(
                ev.timestamp,
                ev.sku,
                ev.seller[:16],
                f"${ev.amount:.2f}",
                f"[{tier_color}]{ev.acf_tier}[/{tier_color}]",
                f"[{outcome_color}]{ev.outcome}[/{outcome_color}]",
                ev.fiat_ref[:24] if ev.fiat_ref != "N/A" else "[dim]N/A[/dim]",
            )

        layout["events"].update(Panel(e_table, title="Payment Events", border_style="white"))

        return Panel(layout, border_style="dim")
