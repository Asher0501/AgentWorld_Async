"""Session — SQLite backend with ring buffer and periodic batch flush."""

import sqlite3
import asyncio
import time
import json
import os
from collections import deque


SCHEMA_TICKS = """
CREATE TABLE IF NOT EXISTS ticks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session    TEXT    NOT NULL,
    agent      TEXT    NOT NULL,
    phase      TEXT    NOT NULL,
    wall_ts    REAL    NOT NULL,
    sim_time   REAL,
    tick_n     INTEGER DEFAULT 0,
    g_triggered INTEGER DEFAULT 0,
    g_reason    TEXT,
    g_zone      TEXT,
    g_nearby    INTEGER,
    g_drives    TEXT,
    d_action    TEXT,
    d_intent    TEXT,
    d_target    TEXT,
    d_tokens    INTEGER,
    d_latency   REAL,
    d_retries   INTEGER DEFAULT 0,
    r_narrative   TEXT,
    r_deltas      TEXT,
    r_thread_done INTEGER DEFAULT 0,
    r_duration    REAL,
    r_file        TEXT
);
CREATE INDEX IF NOT EXISTS idx_ticks_agent ON ticks(session, agent);
"""

SCHEMA_ERRORS = """
CREATE TABLE IF NOT EXISTS errors (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    session   TEXT    NOT NULL,
    agent     TEXT,
    module    TEXT    NOT NULL,
    message   TEXT    NOT NULL,
    count     INTEGER DEFAULT 1,
    first_at  REAL,
    last_at   REAL,
    traceback TEXT
);
CREATE INDEX IF NOT EXISTS idx_errors_module ON errors(session, module);
"""

SCHEMA_LLM = """
CREATE TABLE IF NOT EXISTS llm_calls (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session    TEXT    NOT NULL,
    provider   TEXT,
    latency_ms REAL    NOT NULL,
    tokens     INTEGER DEFAULT 0,
    error      INTEGER DEFAULT 0,
    wall_ts    REAL    NOT NULL
);
"""


class Session:
    """SQLite-backed observer.  Writes are sync (~5µs ring-buffer append);
    batch flush is periodic (background task, ~5ms for 100 rows)."""

    def __init__(self, storage: str, buffer_size: int = 100,
                 flush_interval: float = 5.0):
        self._storage = storage
        self._buffer_size = buffer_size
        self._flush_interval = flush_interval
        self._session_id = os.path.basename(storage).replace(".sqlite3", "").replace(".db", "")

        os.makedirs(os.path.dirname(storage) or ".", exist_ok=True)
        self._conn = sqlite3.connect(storage, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.executescript(SCHEMA_TICKS)
        self._conn.executescript(SCHEMA_ERRORS)
        self._conn.executescript(SCHEMA_LLM)
        self._conn.commit()

        self._buffer: deque[dict] = deque(maxlen=buffer_size)
        self._tick_counter: dict[str, int] = {}
        self._total_written = 0
        self._running = True
        try:
            loop = asyncio.get_running_loop()
            self._flush_task = loop.create_task(self._flush_loop())
        except RuntimeError:
            self._flush_task = None  # no event loop — tests/scripts run sync

    # ── public: called synchronously from hooks ──

    def write(self, **kwargs):
        """Append one structured row to ring buffer.  Sync, ~5µs."""
        kwargs.setdefault("session", self._session_id)
        kwargs.setdefault("wall_ts", time.time())
        agent = kwargs.get("agent", "unknown")
        n = self._tick_counter.get(agent, 0) + 1
        self._tick_counter[agent] = n
        kwargs["tick_n"] = n
        self._buffer.append(kwargs)
        if len(self._buffer) >= self._buffer_size:
            self._flush()

    # ── flush ──

    async def _flush_loop(self):
        while self._running:
            await asyncio.sleep(self._flush_interval)
            if self._buffer:
                self._flush()

    def _flush(self):
        """Batch-insert all buffered rows (sync, called from main thread)."""
        if not self._buffer:
            return
        batch = list(self._buffer)
        self._buffer.clear()

        tick_rows = []
        error_rows = []
        llm_rows = []
        warning_rows = []

        for row in batch:
            phase = row.get("phase", "")
            if phase in ("gate", "decide", "result"):
                tick_rows.append(row)
            elif phase == "error":
                error_rows.append(row)
            elif phase == "llm":
                llm_rows.append(row)
            elif phase == "warning":
                warning_rows.append(row)

        if tick_rows:
            self._write_ticks(tick_rows)
        if error_rows:
            self._dedup_errors(error_rows)
        if llm_rows:
            self._write_llm(llm_rows)
        if warning_rows:
            self._dedup_errors(warning_rows)

        self._conn.commit()
        self._total_written += len(batch)

    def _write_ticks(self, rows: list[dict]):
        placeholders = ", ".join(["?"] * 22)
        self._conn.executemany(
            f"INSERT INTO ticks "
            f"(session,agent,phase,wall_ts,sim_time,tick_n,"
            f"g_triggered,g_reason,g_zone,g_nearby,g_drives,"
            f"d_action,d_intent,d_target,d_tokens,d_latency,d_retries,"
            f"r_narrative,r_deltas,r_thread_done,r_duration,r_file) "
            f"VALUES ({placeholders})",
            [self._tick_tuple(r) for r in rows])

    def _tick_tuple(self, r: dict) -> tuple:
        return (
            r.get("session", ""), r.get("agent", ""), r.get("phase", ""),
            r.get("wall_ts", 0), r.get("sim_time"), r.get("tick_n", 0),
            r.get("g_triggered"), r.get("g_reason"), r.get("g_zone"),
            r.get("g_nearby"), r.get("g_drives"),
            r.get("d_action"), r.get("d_intent"), r.get("d_target"),
            r.get("d_tokens"), r.get("d_latency"), r.get("d_retries"),
            r.get("r_narrative"), r.get("r_deltas"), r.get("r_thread_done"),
            r.get("r_duration"), r.get("r_file"),
        )

    def _write_llm(self, rows: list[dict]):
        self._conn.executemany(
            "INSERT INTO llm_calls (session,provider,latency_ms,tokens,error,wall_ts) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [(r.get("session",""), r.get("provider",""), r.get("latency_ms",0),
              r.get("tokens",0), r.get("error",0), r.get("wall_ts", 0))
             for r in rows])

    def _dedup_errors(self, rows: list[dict]):
        for r in rows:
            module = r.get("module", "")
            message = r.get("message", "")
            key_msg = message[:120]
            cur = self._conn.execute(
                "SELECT id, count FROM errors WHERE session=? AND module=? AND SUBSTR(message,1,120)=?",
                (self._session_id, module, key_msg))
            existing = cur.fetchone()
            if existing:
                cur.execute(
                    "UPDATE errors SET count=?, last_at=? WHERE id=?",
                    (existing[1] + 1, r.get("wall_ts", 0), existing[0]))
            else:
                self._conn.execute(
                    "INSERT INTO errors (session,agent,module,message,count,first_at,last_at,traceback) "
                    "VALUES (?,?,?,?,1,?,?,?)",
                    (self._session_id, r.get("agent"), module, message,
                     r.get("wall_ts", 0), r.get("wall_ts", 0), r.get("traceback", "")))

    # ── summary ──

    def summary(self) -> dict:
        """Return aggregate summary. Flushes buffer first."""
        self._flush()  # sync buffered rows before counting
        cur = self._conn.execute("SELECT COUNT(*) FROM ticks")
        total_ticks = cur.fetchone()[0]
        cur = self._conn.execute("SELECT COUNT(*) FROM errors")
        total_errors = cur.fetchone()[0]
        cur = self._conn.execute("SELECT COUNT(*) FROM llm_calls")
        total_llm = cur.fetchone()[0]
        cur = self._conn.execute("SELECT phase, COUNT(*) FROM ticks GROUP BY phase")
        phase_counts = dict(cur.fetchall())
        return {
            "total_ticks": total_ticks,
            "total_errors": total_errors,
            "total_llm_calls": total_llm,
            "phase_counts": phase_counts,
            "total_written": self._total_written,
        }

    def dump(self) -> str:
        s = self.summary()
        lines = [
            f"Logger Session: {self._session_id}",
            f"  Ticks: {s['total_ticks']} "
            f"(gate={s['phase_counts'].get('gate',0)}, "
            f"decide={s['phase_counts'].get('decide',0)}, "
            f"result={s['phase_counts'].get('result',0)})",
            f"  Errors: {s['total_errors']}",
            f"  LLM calls: {s['total_llm_calls']}",
            f"  Storage: {self._storage}",
        ]
        return "\n".join(lines)

    def close(self):
        """Flush remaining buffer and close DB. Works in both sync and async contexts."""
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
        self._flush()
        self._conn.close()
