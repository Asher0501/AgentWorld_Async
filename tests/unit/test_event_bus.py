"""Unit tests for EventBus — pure async queue, no filesystem, no LLM."""
import asyncio
import pytest
from event_bus import EventBus


def test_emit_and_history():
    eb = EventBus(history_size=10)
    eb.emit({"agent": "test", "action_text": "hello"})
    assert len(eb._history) == 1
    assert eb._history[0]["agent"] == "test"


@pytest.mark.asyncio
async def test_register_returns_queue_with_history():
    eb = EventBus(history_size=10)
    eb.emit({"msg": "hello"})
    eb.emit({"msg": "world"})

    q = await eb.register()  # creates queue, replays history
    e1_raw = await asyncio.wait_for(q.get(), timeout=1)
    e2_raw = await asyncio.wait_for(q.get(), timeout=1)
    import json
    e1 = json.loads(e1_raw)
    e2 = json.loads(e2_raw)
    assert e1["msg"] == "hello"
    assert e2["msg"] == "world"


@pytest.mark.asyncio
async def test_emit_delivers_to_registered_client():
    eb = EventBus(history_size=10)
    q = await eb.register()
    eb.emit({"msg": "live"})
    raw = await asyncio.wait_for(q.get(), timeout=1)
    import json
    event = json.loads(raw)
    assert event["msg"] == "live"


@pytest.mark.asyncio
async def test_queue_full_handled_gracefully():
    """Fill queue to capacity — emit should not crash, just drop for this client."""
    eb = EventBus(history_size=10)
    q = await eb.register()
    # Fill to capacity (200) without consuming
    for i in range(201):
        eb.emit({"n": i})
    # Should not have crashed — queue overflow silently dropped for this client
    # Other clients unaffected
    q2 = await eb.register()
    raw = await asyncio.wait_for(q2.get(), timeout=1)
    import json
    # q2 gets history replay starting from oldest in window
    assert json.loads(raw)["n"] >= 0


@pytest.mark.asyncio
async def test_unregister_stops_delivery():
    eb = EventBus(history_size=10)
    q = await eb.register()
    eb.unregister(q)
    eb.emit({"msg": "should not be received"})
    assert q.empty()


def test_history_size_cap():
    eb = EventBus(history_size=3)
    for i in range(5):
        eb.emit({"n": i})
    assert len(eb._history) == 3
    assert eb._history[0]["n"] == 2  # oldest is dropped
