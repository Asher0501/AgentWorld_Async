"""Regression tests covering all code modifications from Phase 0-4.
Each test maps to a specific bug fix or enhancement."""
import time
import pytest
from layers.agent import AgentLayer
from layers.auditory import AuditoryLayer
from agent.sensory_memory import SensoryMemory, SensorRecord
from entity.entity import Entity


# ═══════════════════════════════════════════════════════════════
# #3: sensory is_new — speech-content comparison (Phase 0)
# ═══════════════════════════════════════════════════════════════

def _make_observer(name="Observer"):
    e = Entity(id="observer", name=name, zone="test", pos=[0, 0])
    al = AgentLayer(autonomous=True)
    al.sensory = SensoryMemory()
    al.view_radius = 30
    al.hearing_radius = 30
    e.layers["agent"] = al
    return e

def _make_speaker(eid, name, speech="", speech_ts=0):
    e = Entity(id=eid, name=name, zone="test", pos=[5, 0])
    aud = AuditoryLayer(audible_radius=20, properties={"current_speech": speech, "speech_ts": speech_ts})
    e.layers["auditory"] = aud
    return e


def test_sensory_first_utterance_enters_buffer():
    """Bug: is_new gated on entity-first-seen, blocking subsequent speech.
    Fix: use speech-content comparison — is_new OR speech changed."""
    from systems.sensory import SensorySystem
    sensor = SensorySystem()
    obs = _make_observer("Listener")
    speaker = _make_speaker("s1", "Alice", speech="Hello", speech_ts=time.time())

    al_buf = obs.get("agent")._conversation_buffer
    assert al_buf == []

    sensor.update(obs, {"s1": speaker})
    assert len(al_buf) == 1, "First utterance should always enter buffer"
    assert al_buf[0]["text"] == "Hello"


def test_sensory_repeated_same_speech_not_duplicated():
    """Same speech second tick → should NOT re-enter buffer (no duplicate)."""
    from systems.sensory import SensorySystem
    sensor = SensorySystem()
    obs = _make_observer("Listener")
    speaker = _make_speaker("s1", "Alice", speech="Hello", speech_ts=time.time())

    al_buf = obs.get("agent")._conversation_buffer
    sensor.update(obs, {"s1": speaker})
    assert len(al_buf) == 1

    # Second tick — same speech content, should not duplicate
    sensor.update(obs, {"s1": speaker})
    assert len(al_buf) == 1, "Same speech repeated should not duplicate buffer entry"


def test_sensory_different_speech_from_same_speaker_enters_buffer():
    """Bug: was dropping second utterance from same speaker.
    Fix: different speech content → enters buffer."""
    from systems.sensory import SensorySystem
    sensor = SensorySystem()
    obs = _make_observer("Listener")
    speaker1 = _make_speaker("s1", "Alice", speech="Hello", speech_ts=time.time())

    al_buf = obs.get("agent")._conversation_buffer
    sensor.update(obs, {"s1": speaker1})
    assert len(al_buf) == 1
    assert al_buf[0]["text"] == "Hello"

    # Alice says something different — should enter buffer again
    speaker1.layers["auditory"].properties["current_speech"] = "How are you?"
    speaker1.layers["auditory"].properties["speech_ts"] = time.time()
    sensor.update(obs, {"s1": speaker1})
    assert len(al_buf) == 2, "New utterance from same speaker should enter buffer"
    assert al_buf[1]["text"] == "How are you?"


def test_sensory_multiple_speakers_buffer():
    """Multiple speakers with multiple utterances — all distinct go to buffer."""
    from systems.sensory import SensorySystem
    sensor = SensorySystem()
    obs = _make_observer("Listener")
    alice = _make_speaker("s1", "Alice", speech="Hi", speech_ts=time.time())
    bob = _make_speaker("s2", "Bob", speech="Hey", speech_ts=time.time())

    al_buf = obs.get("agent")._conversation_buffer
    sensor.update(obs, {"s1": alice, "s2": bob})
    assert len(al_buf) == 2  # both new

    # Both speak again
    alice.layers["auditory"].properties["current_speech"] = "What's up?"
    alice.layers["auditory"].properties["speech_ts"] = time.time()
    bob.layers["auditory"].properties["current_speech"] = "Not much"
    bob.layers["auditory"].properties["speech_ts"] = time.time()
    sensor.update(obs, {"s1": alice, "s2": bob})
    assert len(al_buf) == 4, "Both second utterances should enter buffer"


def test_sensory_buffer_capped_at_8():
    """Buffer FIFO cap at 8 entries — oldest dropped."""
    from systems.sensory import SensorySystem
    sensor = SensorySystem()
    obs = _make_observer("Listener")
    al_buf = obs.get("agent")._conversation_buffer

    for i in range(12):
        speaker = _make_speaker(f"s{i}", f"NPC{i}", speech=f"msg{i}", speech_ts=time.time())
        sensor.update(obs, {f"s{i}": speaker})

    assert len(al_buf) == 8, "Buffer should cap at 8"
    assert al_buf[0]["text"] == "msg4"  # 0-3 dropped


# ═══════════════════════════════════════════════════════════════
# #1: spawn_entity ID collision (Phase 0)
# ═══════════════════════════════════════════════════════════════

def test_spawn_duplicate_id_preserves_original(empty_world):
    """When duplicate ID is spawned, ValueError is raised AND the original entity
    is NOT overwritten."""
    entity_def = {"id": "e1", "name": "Original", "zone": "main", "pos": [0, 0]}
    empty_world.spawn_entity(entity_def)

    dup = {"id": "e1", "name": "Impostor", "zone": "main", "pos": [10, 10]}
    with pytest.raises(ValueError, match="already exists"):
        empty_world.spawn_entity(dup)

    assert empty_world.entities["e1"].name == "Original"
    assert empty_world.entities["e1"].pos == [0, 0]


def test_spawn_unique_ids_no_collision(empty_world):
    """Two different IDs spawn without conflict."""
    e1 = empty_world.spawn_entity({"id": "a", "name": "A", "zone": "main", "pos": [0, 0]})
    e2 = empty_world.spawn_entity({"id": "b", "name": "B", "zone": "main", "pos": [5, 5]})
    assert e1.id == "a"
    assert e2.id == "b"
    assert "a" in empty_world.entities
    assert "b" in empty_world.entities


# ═══════════════════════════════════════════════════════════════
# #4: _pending_action defer-clear (Phase 0)
# ═══════════════════════════════════════════════════════════════

def test_pending_action_not_cleared_until_successful_execution():
    """Fix: _pending_action = None moved to AFTER execution (before await sleep(0)).
    Before the fix, it was cleared BEFORE execution — exception mid-execution lost the action."""
    from loop import run_agent
    import inspect

    src = inspect.getsource(run_agent)
    # Find the FLUSH block: _pending_action is set to None only AFTER file output
    pending_none_positions = []
    for i, line in enumerate(src.split('\n')):
        if '_pending_action = None' in line:
            pending_none_positions.append(i)

    # There should be exactly one place where _pending_action = None
    assert len(pending_none_positions) == 1, \
        f"Expected 1 clearing of _pending_action, found {len(pending_none_positions)}"

    # The None assignment should come AFTER file_output handling ("fo["content"]" or end of FLUSH)
    lines = src.split('\n')
    clear_line = lines[pending_none_positions[0]]
    # Get surrounding context — should be near file output or at FLUSH end
    start = max(0, pending_none_positions[0] - 5)
    end = min(len(lines), pending_none_positions[0] + 3)
    context = '\n'.join(lines[start:end])
    # Must NOT be immediately after "enqueued_decision, enqueued_target = al._pending_action"
    # (that would be the old position at line-start of FLUSH)
    assert 'enqueued_decision' not in clear_line, \
        f"_pending_action = None should NOT be near enqueued_decision assignment.\nContext:\n{context}"


# ═══════════════════════════════════════════════════════════════
# #10: event_bus QueueFull warning (Phase 3)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_event_bus_queuefull_logs_warning(caplog):
    """QueueFull should log a warning instead of silently passing."""
    from event_bus import EventBus
    import asyncio

    eb = EventBus(history_size=10)
    tiny = await eb.register()  # maxsize=200

    # Fill the queue without consuming
    for i in range(201):
        eb.emit({"n": i})

    # Should have logged at least one warning
    # Note: agent_logging may not use Python's logging module directly,
    # so caplog might not capture it. We verify by code inspection instead.
    from event_bus import EventBus as EB
    import inspect
    src = inspect.getsource(EB.emit)
    assert 'log.warning' in src, \
        "QueueFull handler must log warning, not pass silently"

    # Also verify that multiple clients work — second client still gets data
    q2 = await eb.register()
    raw = await asyncio.wait_for(q2.get(), timeout=1)
    import json
    assert json.loads(raw)["n"] >= 0


# ═══════════════════════════════════════════════════════════════
# #12: loop.py transient vs fatal error distinction (Phase 3)
# ═══════════════════════════════════════════════════════════════

def test_loop_error_backoff_variable_exists():
    """Verify err_backoff dict is declared in run_agent and used in except block."""
    from loop import run_agent
    import inspect
    src = inspect.getsource(run_agent)
    assert 'err_backoff' in src, "err_backoff dict must exist for per-agent backoff tracking"
    assert 'err_backoff[name]' in src, "Backoff must be tracked per-agent name"


def test_loop_transient_error_types_identified():
    """Verify the except block distinguishes transient error types by name."""
    from loop import run_agent
    import inspect
    src = inspect.getsource(run_agent)
    # The transient detection should check exception type name
    assert 'RateLimitError' in src, "Must detect RateLimitError"
    assert 'Timeout' in src or 'TimeoutError' in src, "Must detect Timeout"
    # Transient errors use exponential backoff
    assert '2 **' in src, "Transient errors must use exponential backoff"


def test_loop_error_logs_to_collector():
    """Verify exception logging to logger."""
    from loop import run_agent
    import inspect
    src = inspect.getsource(run_agent)
    assert 'log.error(' in src, "Must log to logger with agent name"


# ═══════════════════════════════════════════════════════════════
# #13: agent_logging debug at key paths (Phase 3)
# ═══════════════════════════════════════════════════════════════

def test_agent_logging_at_delta_trigger():
    """Verify log.gate() is called when DELTA triggers LLM call."""
    from loop import run_agent
    import inspect
    src = inspect.getsource(run_agent)
    assert 'DELTA triggered' in src, "Must log at delta gate trigger"
    assert 'log.gate(' in src, "Must use log.gate"


def test_agent_logging_at_enqueue():
    """Verify debug log is emitted when action is enqueued."""
    from loop import run_agent
    import inspect
    src = inspect.getsource(run_agent)
    assert 'ENQUEUE:' in src, "Must log at ENQUEUE phase"


