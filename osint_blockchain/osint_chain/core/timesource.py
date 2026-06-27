"""Trusted time source with NTP synchronisation and timestamp authority.

Each block records *when* it was created together with the authority that
vouches for that time. When NTP is reachable, the timestamp authority is the
queried NTP server and an ``ntp_offset`` (seconds between local and NTP time)
is recorded so auditors can assess clock drift. When NTP is unreachable the
block falls back to the local system clock and clearly labels the authority
as ``local-system-clock`` so the reduced trust level is explicit.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional

try:
    import ntplib  # type: ignore
except ImportError:  # pragma: no cover
    ntplib = None


@dataclass
class TimeStamp:
    """A timestamp annotated with its trust authority."""

    iso: str  # ISO-8601 UTC string
    unix: float  # POSIX seconds
    authority: str  # NTP server hostname or "local-system-clock"
    source: str  # "ntp" | "local"
    ntp_offset: Optional[float] = None  # local - ntp, seconds (None if local)

    def to_dict(self) -> dict:
        return asdict(self)


class TimeSource:
    """Resolves trusted timestamps, querying NTP when enabled/available."""

    def __init__(
        self,
        servers: Optional[List[str]] = None,
        timeout: int = 3,
        enabled: bool = True,
    ):
        self.servers = servers or ["pool.ntp.org"]
        self.timeout = timeout
        self.enabled = enabled and ntplib is not None
        self._client = ntplib.NTPClient() if self.enabled else None

    def _query_ntp(self):
        """Try each configured server; return (server, response) or (None, None)."""
        if not self.enabled:
            return None, None
        for server in self.servers:
            try:
                resp = self._client.request(server, version=3, timeout=self.timeout)
                return server, resp
            except Exception:
                continue
        return None, None

    def now(self) -> TimeStamp:
        """Return a trusted timestamp, preferring NTP."""
        server, resp = self._query_ntp()
        if resp is not None:
            unix = resp.tx_time
            dt = datetime.fromtimestamp(unix, tz=timezone.utc)
            return TimeStamp(
                iso=dt.isoformat(),
                unix=unix,
                authority=server,
                source="ntp",
                ntp_offset=round(time.time() - unix, 6),
            )
        # Fallback: local system clock
        unix = time.time()
        dt = datetime.fromtimestamp(unix, tz=timezone.utc)
        return TimeStamp(
            iso=dt.isoformat(),
            unix=unix,
            authority="local-system-clock",
            source="local",
            ntp_offset=None,
        )

    def health(self) -> dict:
        """Diagnostic info about NTP reachability (for the API/CLI)."""
        if not self.enabled:
            return {"ntp_enabled": False, "reachable": False, "reason": "disabled or ntplib missing"}
        server, resp = self._query_ntp()
        if resp is None:
            return {"ntp_enabled": True, "reachable": False, "servers": self.servers}
        return {
            "ntp_enabled": True,
            "reachable": True,
            "authority": server,
            "offset_seconds": round(time.time() - resp.tx_time, 6),
        }
