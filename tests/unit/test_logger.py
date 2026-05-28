"""Logger module unit tests.

Tests 6 hooks, enable/disable lifecycle, SQLite persistence,
error dedup, ring-buffer flush, and env-var auto-enable.
"""

import os
import sys
import json
import sqlite3
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


# ── fixtures ──

@pytest.fixture
def reset_log():
    """Ensure logger starts in disabled state for each test."""
    os.environ.pop("AW_LOG", None)
    from logger import log, disable
    disable()
    yield
    disable()


@pytest.fixture
def tmp_storage():
    """Create a temp SQLite DB path, clean up after."""
    fd, path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(fd)
    os.unlink(path)  # Session will recreate
    yield path
    try:
        os.unlink(path)
        os.unlink(path + "-wal")
        os.unlink(path + "-shm")
    except OSError:
        pass


# ── No-op mode ──

class TestNoOp:
    """Default state: all hooks no-op, no I/O."""

    def test_logger_disabled_by_default(self, reset_log):
        from logger import log
        assert not log.enabled
        assert log.summary() is None
        assert "not enabled" in log.dump().lower()

    def test_all_hooks_noop_no_crash(self, reset_log):
        from logger import log
        log.gate(agent="ross")
        log.decide(agent="ross")
        log.result(agent="ross")
        log.error(agent="ross", module="test")
        log.warning(agent="ross", module="test", message="test")
        log.llm(provider="deepseek", latency_ms=100)
        assert not log.enabled

    def test_noop_does_not_write_files(self, reset_log, tmp_storage):
        from logger import log
        log.gate(agent="ross", triggered=True)
        log.decide(agent="ross", action="walk")
        log.result(agent="ross", action="walk")
        assert not os.path.exists(tmp_storage)


# ── Enable / disable ──

class TestEnableDisable:
    """Toggle lifecycle: enable → write → disable → verify."""

    def test_enable_activates_logger(self, reset_log):
        from logger import log, enable, disable
        assert not log.enabled
        disable()
        assert log._gate.__name__ == "_noop"

    def test_double_enable_idempotent(self, reset_log, tmp_storage):
        from logger import log, enable
        enable(tmp_storage)
        s1 = log._session
        enable(tmp_storage)
        s2 = log._session
        assert s1 is s2
        log.disable()

    def test_double_disable_idempotent(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        disable()
        assert not log.enabled
        disable()
        assert not log.enabled

    def test_enable_then_disable_flushes_data(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        log.gate(agent="ross", triggered=True)
        log.decide(agent="ross", action="walk")
        log.result(agent="ross", action="walk", narrative="hi")
        disable()

        db = sqlite3.connect(tmp_storage)
        rows = list(db.execute("SELECT phase FROM ticks"))
        db.close()
        assert len(rows) == 3

    def test_enabled_true_after_enable(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        assert log.enabled
        disable()
        assert not log.enabled


# ── Individual hooks ──

class TestGate:
    """log.gate() — delta gate trigger status + drives."""

    def test_gate_triggered(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        log.gate(agent="ross", triggered=True, reason="auditory:changed",
                 zone="central_perk", nearby=3,
                 drives={"hunger": 40, "social": 70})
        disable()
        db = sqlite3.connect(tmp_storage)
        row = list(db.execute(
            "SELECT agent, phase, g_triggered, g_reason, g_zone, g_nearby, g_drives FROM ticks"
        ))[0]
        assert row[0] == "ross"
        assert row[1] == "gate"
        assert row[2] == 1
        assert "auditory" in row[3]
        assert row[4] == "central_perk"
        assert row[5] == 3
        assert json.loads(row[6])["social"] == 70
        db.close()

    def test_gate_not_triggered(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        log.gate(agent="ross", triggered=False)
        disable()
        db = sqlite3.connect(tmp_storage)
        row = list(db.execute("SELECT g_triggered FROM ticks"))[0]
        assert row[0] == 0
        db.close()

    def test_gate_empty_defaults(self, reset_log, tmp_storage):
        """All optional params default to empty/0."""
        from logger import log, enable, disable
        enable(tmp_storage)
        log.gate(agent="ross")
        disable()
        db = sqlite3.connect(tmp_storage)
        row = list(db.execute(
            "SELECT g_triggered, g_reason, g_zone, g_nearby, g_drives FROM ticks"
        ))[0]
        assert row == (0, "", "", 0, None)
        db.close()

    def test_gate_drives_none_handled(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        log.gate(agent="ross", drives=None)
        disable()
        db = sqlite3.connect(tmp_storage)
        row = list(db.execute("SELECT g_drives FROM ticks"))[0]
        assert row[0] is None
        db.close()


class TestDecide:
    """log.decide() — LLM decision snapshot."""

    def test_decide_full_params(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        log.decide(agent="ross", action="走向Rachel，拍拍她肩膀",
                   intent="跟Rachel打招呼", target="Rachel",
                   tokens=1520, latency=2340.0, retries=1)
        disable()
        db = sqlite3.connect(tmp_storage)
        row = list(db.execute(
            "SELECT agent, phase, d_action, d_intent, d_target, d_tokens, d_latency, d_retries FROM ticks"
        ))[0]
        assert row[0] == "ross"
        assert row[1] == "decide"
        assert "Rachel" in row[2]
        assert "打招呼" in row[3]
        assert row[4] == "Rachel"
        assert row[5] == 1520
        assert row[6] == 2340.0
        assert row[7] == 1
        db.close()

    def test_decide_minimal_params(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        log.decide(agent="phoebe")
        disable()
        db = sqlite3.connect(tmp_storage)
        row = list(db.execute(
            "SELECT d_action, d_intent, d_target, d_tokens, d_latency, d_retries FROM ticks"
        ))[0]
        assert row == ("", "", "", 0, 0.0, 0)
        db.close()


class TestResult:
    """log.result() — action execution result."""

    def test_result_full_params(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        log.result(agent="ross", action="搭话", target="Rachel",
                   narrative="Ross对Rachel说了嘿，最近怎么样？",
                   deltas={"social": 5, "fun": 3},
                   sim=5.63, thread_done=True, duration=3.0,
                   file_output={"filename": "coder_01_test.py"})
        disable()
        db = sqlite3.connect(tmp_storage)
        row = list(db.execute(
            "SELECT d_action, d_target, r_narrative, r_deltas, sim_time, "
            "r_thread_done, r_duration, r_file FROM ticks"
        ))[0]
        assert row[0] == "搭话"
        assert row[1] == "Rachel"
        assert "嘿" in row[2]
        assert json.loads(row[3])["social"] == 5
        assert row[4] == 5.63
        assert row[5] == 1
        assert row[6] == 3.0
        assert row[7] == "coder_01_test.py"
        db.close()

    def test_result_file_output_none(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        log.result(agent="ross", file_output=None)
        disable()
        db = sqlite3.connect(tmp_storage)
        row = list(db.execute("SELECT r_file FROM ticks"))[0]
        assert row[0] is None
        db.close()


class TestError:
    """log.error() — exception capture with dedup."""

    def test_error_from_exception(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        try:
            raise ValueError("test boom")
        except ValueError as e:
            log.error(agent="ross", module="loop.ross", exception=e)
        disable()
        db = sqlite3.connect(tmp_storage)
        row = list(db.execute(
            "SELECT module, message, count, agent FROM errors"
        ))[0]
        assert row[0] == "loop.ross"
        assert "ValueError" in row[1]
        assert "test boom" in row[1]
        assert row[2] == 1
        assert row[3] == "ross"
        db.close()

    def test_error_from_message(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        log.error(module="verification", message="bounds check failed")
        disable()
        db = sqlite3.connect(tmp_storage)
        row = list(db.execute("SELECT message, traceback FROM errors"))[0]
        assert "bounds check" in row[0]
        assert row[1] == "" or row[1] is None
        db.close()

    def test_error_dedup_same_module_message(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        for _ in range(3):
            try:
                raise RuntimeError("rate limit")
            except RuntimeError as e:
                log.error(agent="ross", module="loop.ross", exception=e)
        disable()
        db = sqlite3.connect(tmp_storage)
        row = list(db.execute("SELECT count FROM errors"))[0]
        assert row[0] == 3  # merged count
        db.close()

    def test_error_different_module_separate(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        try:
            raise ValueError("boom")
        except ValueError as e:
            log.error(module="loop.ross", exception=e)
            log.error(module="llm.client", exception=e)
        disable()
        db = sqlite3.connect(tmp_storage)
        rows = list(db.execute("SELECT module FROM errors"))
        assert len(rows) == 2
        modules = {r[0] for r in rows}
        assert "loop.ross" in modules
        assert "llm.client" in modules
        db.close()

    def test_error_traceback_preserved(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        try:
            1 / 0
        except ZeroDivisionError as e:
            log.error(module="test", exception=e)
        disable()
        db = sqlite3.connect(tmp_storage)
        row = list(db.execute("SELECT traceback FROM errors"))[0]
        assert "ZeroDivisionError" in row[0]
        assert "division by zero" in row[0]
        db.close()


class TestWarning:
    """log.warning() — non-fatal warnings."""

    def test_warning_stored(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        log.warning(agent="gunther", module="verification",
                    message="thirst below min: 1.7 + -15 = -13.3")
        disable()
        db = sqlite3.connect(tmp_storage)
        row = list(db.execute("SELECT agent, module, message FROM errors"))[0]
        assert row[0] == "gunther"
        assert row[1] == "verification"
        assert "thirst" in row[2]
        db.close()

    def test_warning_default_agent(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        log.warning(message="test")
        disable()
        db = sqlite3.connect(tmp_storage)
        row = list(db.execute("SELECT agent FROM errors"))[0]
        assert row[0] == "system"
        db.close()

    def test_warning_dedup_same_message(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        for _ in range(5):
            log.warning(module="verification", message="same warning")
        disable()
        db = sqlite3.connect(tmp_storage)
        row = list(db.execute("SELECT count FROM errors"))[0]
        assert row[0] == 5
        db.close()


class TestLLM:
    """log.llm() — per-call latency tracking."""

    def test_llm_success_call(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        log.llm(provider="deepseek", latency_ms=1050.0, tokens=800, error=False)
        disable()
        db = sqlite3.connect(tmp_storage)
        row = list(db.execute(
            "SELECT provider, latency_ms, tokens, error FROM llm_calls"
        ))[0]
        assert row[0] == "deepseek"
        assert row[1] == 1050.0
        assert row[2] == 800
        assert row[3] == 0
        db.close()

    def test_llm_error_call(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        log.llm(provider="minimax", latency_ms=0, tokens=0, error=True)
        disable()
        db = sqlite3.connect(tmp_storage)
        row = list(db.execute("SELECT error FROM llm_calls"))[0]
        assert row[0] == 1
        db.close()

    def test_llm_multiple_calls_recorded(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        for i in range(5):
            log.llm(provider="deepseek", latency_ms=100.0 + i, tokens=100)
        disable()
        db = sqlite3.connect(tmp_storage)
        rows = list(db.execute("SELECT latency_ms FROM llm_calls"))
        assert len(rows) == 5
        latencies = [r[0] for r in rows]
        assert latencies == [100.0, 101.0, 102.0, 103.0, 104.0]
        db.close()


# ── Session — ring buffer & flush ──

class TestSessionFlush:
    """Ring buffer auto-flush on full."""

    def test_buffer_flush_on_full(self, reset_log, tmp_storage):
        """Buffer=10 → 10th entry triggers sync flush."""
        from logger.session import Session
        s = Session(tmp_storage, buffer_size=10, flush_interval=999)
        for i in range(10):
            s.write(agent="ross", phase="decide", d_action=f"action_{i}")
        db = sqlite3.connect(tmp_storage)
        rows = list(db.execute("SELECT d_action FROM ticks ORDER BY id"))
        assert len(rows) == 10
        assert rows[0][0] == "action_0"
        assert rows[9][0] == "action_9"
        db.close()
        s.close()

    def test_close_flushes_remaining(self, reset_log, tmp_storage):
        """close() should flush any un-flushed rows below buffer size."""
        from logger.session import Session
        s = Session(tmp_storage, buffer_size=100, flush_interval=999)
        for i in range(3):
            s.write(agent="ross", phase="gate")
        s.close()
        db = sqlite3.connect(tmp_storage)
        rows = list(db.execute("SELECT phase FROM ticks"))
        assert len(rows) == 3
        db.close()


# ── Multi-phase per-agent ──

class TestMultiPhasePerAgent:
    """All 3 phases for one agent produce 3 distinct rows."""

    def test_full_decision_cycle(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        log.gate(agent="ross", triggered=True, zone="cafe")
        log.decide(agent="ross", action="walk", intent="move")
        log.result(agent="ross", action="walk", narrative="Ross walked to cafe")
        disable()
        db = sqlite3.connect(tmp_storage)
        rows = list(db.execute("SELECT phase, agent FROM ticks ORDER BY id"))
        assert len(rows) == 3
        assert rows[0] == ("gate", "ross")
        assert rows[1] == ("decide", "ross")
        assert rows[2] == ("result", "ross")
        db.close()


# ── Multiple agents ──

class TestMultipleAgents:
    """7 Friends agents, each with full cycles."""

    def test_seven_agents_three_phases(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        agents = ["rachel", "ross", "monica", "chandler", "joey", "phoebe", "gunther"]
        enable(tmp_storage)
        for a in agents:
            log.gate(agent=a, triggered=True, drives={"hunger": 40})
            log.decide(agent=a, action="greet", intent="talk", target=a)
            log.result(agent=a, action="greet", narrative=f"{a} said hi")
        disable()
        db = sqlite3.connect(tmp_storage)
        rows = list(db.execute("SELECT DISTINCT agent FROM ticks ORDER BY agent"))
        assert len(rows) == 7
        assert sorted([r[0] for r in rows]) == sorted(agents)
        db.close()

    def test_per_agent_tick_counter(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        for _ in range(3):
            log.gate(agent="ross")
        for _ in range(5):
            log.gate(agent="rachel")
        disable()
        db = sqlite3.connect(tmp_storage)
        ross_ticks = list(db.execute(
            "SELECT tick_n FROM ticks WHERE agent='ross' ORDER BY id"))
        rachel_ticks = list(db.execute(
            "SELECT tick_n FROM ticks WHERE agent='rachel' ORDER BY id"))
        assert ross_ticks[-1][0] == 3
        assert rachel_ticks[-1][0] == 5
        db.close()


# ── Summary / dump ──

class TestSummary:
    """log.summary() and log.dump() output."""

    def test_summary_returns_dict_when_enabled(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        log.gate(agent="ross")
        log.decide(agent="ross")
        log.result(agent="ross")
        log.llm(provider="deepseek", latency_ms=100)
        s = log.summary()
        assert isinstance(s, dict)
        assert s["total_ticks"] == 3
        assert s["total_llm_calls"] == 1
        assert s["total_written"] == 4
        disable()

    def test_summary_none_when_disabled(self, reset_log):
        from logger import log
        assert log.summary() is None

    def test_dump_contains_session_info(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        log.gate(agent="ross")
        d = log.dump()
        assert "Logger Session:" in d
        assert "Ticks:" in d
        assert "Storage:" in d
        disable()

    def test_dump_when_disabled(self, reset_log):
        from logger import log
        assert "not enabled" in log.dump().lower()

    def test_phase_counts_in_summary(self, reset_log, tmp_storage):
        from logger import log, enable, disable
        enable(tmp_storage)
        log.gate(agent="ross")
        log.gate(agent="ross")
        log.decide(agent="ross")
        log.result(agent="ross")
        log.result(agent="ross")
        log.result(agent="ross")
        s = log.summary()
        pc = s["phase_counts"]
        assert pc["gate"] == 2
        assert pc["decide"] == 1
        assert pc["result"] == 3
        disable()


# ── AW_LOG env var ──

class TestEnvVar:
    """AW_LOG = path → auto-enable on import."""

    def test_aw_log_env_auto_enable(self, reset_log):
        os.environ["AW_LOG"] = "data/logs/test_env.sqlite3"
        try:
            # Clear cached imports and re-import
            import sys
            for mod in list(sys.modules):
                if mod.startswith("logger"):
                    del sys.modules[mod]
            from logger import log, disable
            assert log.enabled, f"Expected enabled, got {log.enabled}"
            log.gate(agent="test")
            log.gate(agent="test")
            log.decide(agent="test")
            s = log.summary()
            assert s["total_ticks"] == 3
            disable()
            # Clean up db file
            import time
            time.sleep(0.1)
            try:
                os.unlink("data/logs/test_env.sqlite3")
                os.unlink("data/logs/test_env.sqlite3-wal")
                os.unlink("data/logs/test_env.sqlite3-shm")
            except OSError:
                pass
        finally:
            os.environ.pop("AW_LOG", None)
            # Re-import clean version
            import sys
            for mod in list(sys.modules):
                if mod.startswith("logger"):
                    del sys.modules[mod]

    def test_no_aw_log_env_no_auto_enable(self, reset_log):
        os.environ.pop("AW_LOG", None)
        import importlib
        import logger.hooks as hooks
        importlib.reload(hooks)
        from logger import log
        assert not log.enabled


# ── Module exports ──

class TestExports:
    """Public API symbols are importable."""

    def test_exports(self):
        from logger import log, enable, disable, Session
        assert callable(enable)
        assert callable(disable)
        assert Session is not None
        assert hasattr(log, "gate")
        assert hasattr(log, "decide")
        assert hasattr(log, "result")
        assert hasattr(log, "error")
        assert hasattr(log, "warning")
        assert hasattr(log, "llm")
        assert hasattr(log, "enable")
        assert hasattr(log, "disable")
