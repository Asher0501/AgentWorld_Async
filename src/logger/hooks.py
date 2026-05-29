"""Hook definitions — 6 observation points with macro-style enable/disable."""

import os
import time
import traceback
import json


def _noop(**kwargs):
    """Default no-op. ~50ns."""
    pass


class Log:
    """Six structured observation hooks.

    Default: all 6 hooks forward to _noop (pass).
    enable(storage) → create SQLite Session, swap implementations.
    disable() → flush + close Session, swap back to _noop.

    All hook methods are synchronous — the ring buffer write is ~5µs.
    Batch flush happens in background (periodic task or on disable).
    """

    def __init__(self):
        self._gate     = _noop
        self._decide   = _noop
        self._result   = _noop
        self._error_fn  = _noop
        self._warning = _noop
        self._llm_fn = _noop
        self._info   = _noop
        self._session = None
        self._enabled = False

    # ── public hook methods (sync) ──

    def gate(self, agent: str, *, triggered: bool = False,
             reason: str = "", zone: str = "",
             nearby: int = 0, drives: dict = None,
             pos: tuple = None, coins: int = 0, **kwargs):
        self._gate(agent=agent, phase="gate",
                   g_triggered=1 if triggered else 0,
                   g_reason=reason or "",
                   g_zone=zone,
                   g_nearby=nearby,
                   g_drives=json.dumps(drives) if drives else None,
                   g_pos_x=pos[0] if pos else None,
                   g_pos_y=pos[1] if pos else None,
                   g_coins=coins,
                   **kwargs)

    def decide(self, agent: str, *, action: str = "", intent: str = "",
               target: str = "", target_id: str = "",
               tokens: int = 0, latency: float = 0.0,
               retries: int = 0, llm_output: dict = None, **kwargs):
        self._decide(agent=agent, phase="decide",
                     d_action=action or "",
                     d_intent=intent or "",
                     d_target=target or "",
                     d_target_id=target_id or "",
                     d_tokens=tokens,
                     d_latency=latency,
                     d_retries=retries,
                     d_llm_output=json.dumps(llm_output) if llm_output else None,
                     **kwargs)

    def result(self, agent: str, *, action: str = "",
               target: str = "", target_id: str = "",
               narrative: str = "",
               deltas: dict = None, sim: float = 0.0,
               thread_done: bool = False, duration: float = 3.0,
               file_output: dict = None, drives: dict = None, **kwargs):
        self._result(agent=agent, phase="result",
                     d_action=action or "",
                     d_target=target or "",
                     d_target_id=target_id or "",
                     r_narrative=narrative or "",
                     r_deltas=json.dumps(deltas) if deltas else None,
                     r_thread_done=1 if thread_done else 0,
                     r_duration=duration,
                     r_file=file_output.get("filename") if file_output else None,
                     sim_time=sim,
                     g_drives=json.dumps(drives) if drives else None,
                     **kwargs)

    def error(self, agent: str = "system", *, module: str = "",
              exception: Exception = None, message: str = "", **kwargs):
        if exception:
            msg = f"{type(exception).__name__}: {exception}"
            tb = traceback.format_exc()
        else:
            msg = message
            tb = ""
        self._error_fn(agent=agent, phase="error",
                       module=module, message=msg, traceback=tb,
                       **kwargs)

    def warning(self, agent: str = "system", *, module: str = "",
                message: str = "", **kwargs):
        self._warning(agent=agent, phase="warning",
                      module=module, message=message,
                      **kwargs)

    def info(self, agent: str = "system", *, module: str = "",
             message: str = "", **kwargs):
        self._info(agent=agent, phase="info",
                   module=module, message=message,
                   **kwargs)

    def llm(self, provider: str, latency_ms: float, tokens: int = 0,
            error: bool = False, **kwargs):
        self._llm_fn(agent="llm", phase="llm",
                     provider=provider, latency_ms=latency_ms,
                     tokens=tokens, error=1 if error else 0,
                     **kwargs)

    # ── enable / disable ──

    def enable(self, storage: str):
        if self._enabled:
            return
        from .session import Session
        self._session = Session(storage)
        self._gate      = self._session.write
        self._decide    = self._session.write
        self._result    = self._session.write
        self._error_fn  = self._session.write
        self._warning = self._session.write
        self._llm_fn  = self._session.write
        self._info    = self._session.write
        self._enabled   = True

    def disable(self):
        if not self._enabled:
            return
        self._enabled = False
        self._gate = self._decide = self._result = _noop
        self._error_fn = self._warning = self._llm_fn = self._info = _noop
        s = self._session
        self._session = None
        if s:
            s.close()

    @property
    def enabled(self) -> bool:
        return self._enabled

    def summary(self) -> dict | None:
        if self._session:
            return self._session.summary()
        return None

    def dump(self) -> str:
        if self._session:
            return self._session.dump()
        return "Logger not enabled."


# ── global singleton ──

log = Log()

if os.environ.get("AW_LOG", "").strip():
    log.enable(os.environ["AW_LOG"].strip())


def enable(storage: str):
    log.enable(storage)


def disable():
    log.disable()
