"""Unit tests for Director — permissions, lifecycle. No filesystem, no LLM."""
import pytest
from core.director import Director


@pytest.fixture
def director(minimal_world):
    d = Director(minimal_world)
    return d


def test_freeze_unfreeze(director):
    assert not director.frozen
    director.freeze()
    assert director.frozen
    director.unfreeze()
    assert not director.frozen


def test_is_controlled_false_initially(director):
    assert not director.is_controlled("agent_1")


def test_take_and_release(director):
    director.take("agent_1", level=2)
    assert director.is_controlled("agent_1")
    director.release("agent_1")
    assert not director.is_controlled("agent_1")


def test_order_and_pending(director):
    director.take("agent_1", level=2)
    decision = {"action": "walk to desk"}
    director.order("agent_1", decision)
    assert director.pending("agent_1") == decision
    assert director.pending("agent_1") is None  # consumed


def test_pending_returns_none_when_not_controlled(director):
    assert director.pending("agent_1") is None


def test_take_nonexistent_agent(director):
    """take() stores by ID without validation — agent loop checks existence."""
    director.take("nonexistent", level=2)
    assert director.is_controlled("nonexistent")
    director.release("nonexistent")
    assert not director.is_controlled("nonexistent")


def test_snap_structure(director):
    snap = director.snap("agent_1")
    assert snap["name"] == "Alice"
    assert snap["zone"] == "test_zone"
    assert "pos" in snap
    assert "memory" in snap


def test_set_and_memorize(director):
    director.take("agent_1", level=2)
    director.set("agent_1", "agent.main_thread", "find food")
    director.memorize("agent_1", "I should eat")
    snap = director.snap("agent_1")
    assert snap["main_thread"] == "find food"
    assert len(snap["memory"]) == 1


def test_permission_level_rejects_write(director):
    director.take("agent_1", level=1)  # observer — can't write
    with pytest.raises(PermissionError):
        director.set("agent_1", "agent.pos", [50, 50])
