"""Logger — unified observability module for AgentWorld Async.

6 hook points, macro-style enable/disable, SQLite backend.
All hooks are synchronous (ring-buffer append, ~5µs).
Batch flush to SQLite happens in background task or on disable().

Usage:
    from logger import log, enable, disable

    enable("data/logs/session_001.sqlite3")

    log.gate(agent="Ross", triggered=True, reason="auditory:changed",
             zone="central_perk", nearby=3, drives={"hunger": 40})

    log.decide(agent="Ross", action="走向Rachel", intent="搭话",
               target="Rachel", tokens=1520, latency=2340.0)

    log.result(agent="Ross", action="搭话", target="Rachel",
               narrative="Ross对Rachel说了嘿...", deltas={"social": 5},
               sim=5.63, thread_done=False, duration=3.0)

    log.error(agent="Ross", module="loop.Ross", exception=e)
    log.warning(agent="Gunther", module="verification", message="thirst below min")
    log.llm(provider="deepseek", latency_ms=2340.0, tokens=1520, error=False)

    disable()
"""

from .hooks import log, enable, disable
from .session import Session

__all__ = ["log", "enable", "disable", "Session"]
