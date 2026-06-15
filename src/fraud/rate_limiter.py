"""
DNSid-anchored rate limiter for Phase 15.

Design: agent identity (DNSid or IP fallback) is the rate limit key.
Same agent making many requests = legitimate high-frequency pattern.
Many distinct agents making few requests each = bot flood signal.

Two separate counters per identity:
  - request_count: total requests in the current window
  - burst_count:   requests in the last BURST_WINDOW_SECONDS

Both limits are enforced independently.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock


WINDOW_SECONDS      = 60
MAX_REQUESTS_WINDOW = 200   # per identity per minute
BURST_WINDOW_SECONDS = 5
MAX_REQUESTS_BURST  = 30    # per identity per 5 seconds


@dataclass
class _WindowCounter:
    timestamps: list = field(default_factory=list)
    lock: Lock = field(default_factory=Lock)

    def add_and_count(self, window_seconds: int) -> int:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self.lock:
            self.timestamps.append(now)
            self.timestamps = [t for t in self.timestamps if t > cutoff]
            return len(self.timestamps)


_counters: dict[str, _WindowCounter] = defaultdict(_WindowCounter)
_burst_counters: dict[str, _WindowCounter] = defaultdict(_WindowCounter)


@dataclass
class RateLimitResult:
    allowed: bool
    identity: str
    request_count: int
    burst_count: int
    reason: str = ""


def check_rate_limit(agent_dnsid: str | None, client_ip: str = "unknown") -> RateLimitResult:
    """
    Check whether this identity is within rate limits.
    DNSid takes precedence over IP as the identity anchor.
    Returns RateLimitResult with allowed=False if either limit is exceeded.
    """
    identity = agent_dnsid if agent_dnsid else f"ip:{client_ip}"

    request_count = _counters[identity].add_and_count(WINDOW_SECONDS)
    burst_count   = _burst_counters[identity].add_and_count(BURST_WINDOW_SECONDS)

    if burst_count > MAX_REQUESTS_BURST:
        return RateLimitResult(
            allowed=False,
            identity=identity,
            request_count=request_count,
            burst_count=burst_count,
            reason=f"Burst limit exceeded: {burst_count} requests in {BURST_WINDOW_SECONDS}s (max {MAX_REQUESTS_BURST})",
        )

    if request_count > MAX_REQUESTS_WINDOW:
        return RateLimitResult(
            allowed=False,
            identity=identity,
            request_count=request_count,
            burst_count=burst_count,
            reason=f"Window limit exceeded: {request_count} requests in {WINDOW_SECONDS}s (max {MAX_REQUESTS_WINDOW})",
        )

    return RateLimitResult(
        allowed=True,
        identity=identity,
        request_count=request_count,
        burst_count=burst_count,
    )


def reset_for_testing(identity: str | None = None) -> None:
    """Clear counters. Only for use in tests."""
    if identity:
        _counters.pop(identity, None)
        _burst_counters.pop(identity, None)
    else:
        _counters.clear()
        _burst_counters.clear()
