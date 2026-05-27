"""Unit tests for delta_gate.py — P/Q change detection (4 pure functions)."""
import time
import pytest
from agent.sensory_memory import SensorRecord
from core.delta_gate import (
    channel_delta, state_delta, stale_check, total_delta, snapshot_p,
)


TEXT = {
    "kl_entered": "[{channel}] {name} entered",
    "kl_left": "[{channel}] {name} left",
    "kl_changed": "[{channel}] {name} changed",
    "kl_state_cross": "{attr} {arrow}{t}",
    "kl_coin": "coins {sign}{delta}",
    "kl_stale": "stale {stale_timeout}s",
}


class FakeDrives:
    def __init__(self, attrs: dict):
        self.attrs = attrs


class FakeAgentLayer:
    def __init__(self):
        self.p_channels = {}
        self.p_state = {}
        self.p_stale = time.time()


# ── channel_delta ──

def test_channel_delta_entity_entered():
    p = {}
    q = {"e1": SensorRecord(entity_id="e1", name="Alice", data={"msg": "hi"}, distance=3)}
    records = {"e1": "Alice"}
    result = channel_delta("visual", p, q, records, TEXT)
    assert "entered" in result
    assert "Alice" in result


def test_channel_delta_entity_left():
    p = {"e1": SensorRecord(entity_id="e1", name="Alice", data={"msg": "was here"}, distance=3)}
    q = {}
    records = {"e1": "Alice"}
    result = channel_delta("visual", p, q, records, TEXT)
    assert "left" in result


def test_channel_delta_empty_data_treated_as_absent():
    """_extract_data returns {} for both None and empty data → no delta.
    This means entities with truly empty observations are invisible to the gate."""
    p = {"e1": SensorRecord(entity_id="e1", name="Alice", data={}, distance=3)}
    q = {}
    records = {"e1": "Alice"}
    result = channel_delta("visual", p, q, records, TEXT)
    assert result == ""


def test_channel_delta_data_changed():
    p = {"e1": SensorRecord(entity_id="e1", name="Alice", data={"msg": "old"}, distance=3)}
    q = {"e1": SensorRecord(entity_id="e1", name="Alice", data={"msg": "new"}, distance=3)}
    records = {"e1": "Alice"}
    result = channel_delta("visual", p, q, records, TEXT)
    assert "changed" in result


def test_channel_delta_no_change():
    data = {"msg": "same"}
    p = {"e1": SensorRecord(entity_id="e1", name="Alice", data=data, distance=3)}
    q = {"e1": SensorRecord(entity_id="e1", name="Alice", data=data, distance=3)}
    records = {"e1": "Alice"}
    result = channel_delta("visual", p, q, records, TEXT)
    assert result == ""


def test_channel_delta_empty_both():
    assert channel_delta("auditory", {}, {}, {}, TEXT) == ""


def test_channel_delta_dict_input():
    p = {}
    q = {"e1": {"data": {"msg": "entered"}}}
    records = {"e1": "Bob"}
    result = channel_delta("auditory", p, q, records, TEXT)
    assert "entered" in result


def test_channel_delta_none_input():
    p = {"e1": None}
    q = {"e1": SensorRecord(entity_id="e1", name="X", data={"x": 1}, distance=3)}
    records = {"e1": "X"}
    result = channel_delta("visual", p, q, records, TEXT)
    assert "entered" in result


# ── state_delta ──

def test_state_delta_no_cross():
    p = {"drives": {"hunger": 20, "energy": 80}}
    drives = FakeDrives({"hunger": 25.0, "energy": 78.0})
    result = state_delta(p, drives, "coins", TEXT, thresholds=[30, 60, 80])
    assert result == ""


def test_state_delta_crosses_threshold():
    p = {"drives": {"hunger": 25, "energy": 80}}
    drives = FakeDrives({"hunger": 35.0, "energy": 75.0})
    result = state_delta(p, drives, "coins", TEXT, thresholds=[30, 60, 80])
    assert "hunger" in result
    assert "↑" in result


def test_state_delta_crosses_downward():
    p = {"drives": {"hunger": 35, "energy": 80}}
    drives = FakeDrives({"hunger": 25.0, "energy": 75.0})
    result = state_delta(p, drives, "coins", TEXT, thresholds=[30, 60, 80])
    assert "hunger" in result
    assert "↓" in result


def test_state_delta_coin_change():
    p = {"drives": {"energy": 80}, "coins": 100}
    drives = FakeDrives({"energy": 82.0, "coins": 120.0})
    result = state_delta(p, drives, "coins", TEXT, coin_epsilon=5)
    assert "coins" in result
    assert "+20" in result


def test_state_delta_coin_below_epsilon():
    p = {"drives": {"energy": 80}, "coins": 100}
    drives = FakeDrives({"energy": 82.0, "coins": 103.0})
    result = state_delta(p, drives, "coins", TEXT, coin_epsilon=5)
    assert result == ""  # 3 < 5 epsilon


def test_state_delta_updates_p_state():
    p = {"drives": {"hunger": 20}}
    drives = FakeDrives({"hunger": 35.0})  # crosses 30 → triggers
    state_delta(p, drives, "coins", TEXT, thresholds=[30])
    assert p["drives"]["hunger"] == 35.0  # updated in-place


# ── stale_check ──

def test_stale_check_triggered():
    p_stale = time.time() - 40
    result = stale_check(p_stale, TEXT, stale_timeout=30)
    assert "stale" in result


def test_stale_check_not_triggered():
    p_stale = time.time() - 5
    result = stale_check(p_stale, TEXT, stale_timeout=30)
    assert result == ""


# ── total_delta ──

def test_total_delta_composite():
    p = FakeAgentLayer()
    p.p_channels = {}
    p.p_state = {"drives": {}}
    p.p_stale = time.time()

    sensory = FakeAgentLayer()
    sensory.channels = {
        "visual": {"e1": SensorRecord(entity_id="e1", name="Alice", data={"msg": "hi"}, distance=3)},
    }

    drives = FakeDrives({})
    result = total_delta(p, sensory, drives, "coins", TEXT)
    assert "entered" in result  # visual channel picked up new entity


def test_total_delta_updates_p_channels():
    p = FakeAgentLayer()
    sensory = FakeAgentLayer()
    sensory.channels = {
        "visual": {"e1": SensorRecord(entity_id="e1", name="Alice", data={}, distance=3)},
    }
    drives = FakeDrives({})
    total_delta(p, sensory, drives, "coins", TEXT)
    assert "visual" in p.p_channels
    assert "e1" in p.p_channels["visual"]


def test_total_delta_empty_sensory():
    p = FakeAgentLayer()
    sensory = FakeAgentLayer()
    sensory.channels = {}
    drives = FakeDrives({})
    result = total_delta(p, sensory, drives, "coins", TEXT)
    assert result == ""


def test_total_delta_stale_triggers():
    p = FakeAgentLayer()
    p.p_stale = time.time() - 50
    sensory = FakeAgentLayer()
    sensory.channels = {}
    drives = FakeDrives({})
    result = total_delta(p, sensory, drives, "coins", TEXT, stale_timeout=30)
    assert "stale" in result


# ── snapshot_p ──

def test_snapshot_p_updates_stale():
    p = FakeAgentLayer()
    old_stale = p.p_stale = time.time() - 10
    sensory = FakeAgentLayer()
    sensory.channels = {}
    drives = FakeDrives({})
    snapshot_p(p, sensory, drives, "coins", TEXT)
    assert p.p_stale > old_stale
