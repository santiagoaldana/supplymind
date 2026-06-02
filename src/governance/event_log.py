"""
Audit Event Log -- Phase 11 (extended)

Append-only JSONL file log. Every significant event across all layers
is written here as it happens. One JSON object per line.

WHY JSONL (newline-delimited JSON):
  Each line is a valid JSON object. The file can be read line by line
  without loading the entire file into memory. Easy to grep, tail, and
  parse with any tool. Standard format for append-only audit logs.

LOG FILE: logs/audit.jsonl

EVENT SCHEMA:
  {
    "ts":       ISO-8601 timestamp,
    "layer":    "Identity" | "Scoping" | "Approvals" | "Enforcement",
    "event":    string (snake_case event name),
    "entity":   string (agent handle, SKU, mandate ID, etc.),
    "operator": string (who caused this event),
    "detail":   string (human-readable summary),
    "data":     dict (optional structured payload)
  }

DURABILITY:
  Log is flushed on every write. No data is lost if a server crashes
  between events. The file persists across server restarts -- unlike
  in-memory dicts which are empty on every restart.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

LOG_FILE = Path(__file__).parent.parent.parent / "logs" / "audit.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(
    layer:    str,
    event:    str,
    entity:   str,
    operator: str,
    detail:   str,
    data:     Optional[dict] = None,
) -> dict:
    """
    Append one event to the audit log.
    Returns the event dict (useful for callers that want to inspect it).
    Creates the log file and parent directory if they do not exist.
    """
    LOG_FILE.parent.mkdir(exist_ok=True)

    entry = {
        "ts":       _now(),
        "layer":    layer,
        "event":    event,
        "entity":   entity,
        "operator": operator,
        "detail":   detail,
    }
    if data:
        entry["data"] = data

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
        f.flush()

    return entry


def read_log(limit: Optional[int] = None) -> list[dict]:
    """
    Read all events from the log file, oldest first.
    Returns empty list if file does not exist.
    If limit is provided, returns the most recent N events.
    """
    if not LOG_FILE.exists():
        return []

    events = []
    with open(LOG_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    if limit:
        return events[-limit:]
    return events


def clear_log() -> None:
    """Truncate the log file. Used in tests only."""
    if LOG_FILE.exists():
        LOG_FILE.write_text("")
