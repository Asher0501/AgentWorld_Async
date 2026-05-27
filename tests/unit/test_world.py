"""Unit tests for World — entity CRUD. Uses minimal_world fixture from conftest."""
import pytest
from core.world import World
from systems.sensory import SensorySystem
from systems.interaction import InteractionSystem
from systems.decay import DecaySystem


class _StubLLM:
    def __init__(self): pass
    async def chat(self, **kw): return "{}"


@pytest.fixture
def empty_world():
    """World with no entities — clean slate for spawn tests."""
    cfg = {
        "world": {"name": "empty", "start_time": "08:00", "time_scale": 60},
        "zones": [{"id": "main", "width": 50, "height": 50}],
        "entities": [],
    }
    return World(cfg, {
        "sensory": SensorySystem(),
        "interaction": InteractionSystem(_StubLLM(), None),
        "decay": DecaySystem(),
    })


# ── Entity presence ──

def test_entities_loaded(minimal_world):
    assert "agent_1" in minimal_world.entities
    assert "agent_2" in minimal_world.entities
    assert minimal_world.entities["agent_1"].name == "Alice"


def test_zones_loaded(minimal_world):
    assert "test_zone" in minimal_world.zones
    assert "test_zone" in minimal_world.grids


# ── get_nearby_ids ──

def test_get_nearby_ids_returns_nearby(minimal_world):
    ids = minimal_world.get_nearby_ids("test_zone", [10, 10], 30)
    assert "agent_1" in ids
    assert "agent_2" in ids


def test_get_nearby_ids_out_of_range(minimal_world):
    ids = minimal_world.get_nearby_ids("test_zone", [10, 10], 1)
    assert "agent_2" not in ids  # Bob at [20,20], radius 1 from [10,10] → out of range


def test_get_nearby_ids_nonexistent_zone(minimal_world):
    ids = minimal_world.get_nearby_ids("mars", [0, 0], 100)
    assert "agent_1" not in ids  # fallback: scan all entities in unknown zone


# ── spawn_entity ──

def test_spawn_entity_success(empty_world):
    entity_def = {
        "id": "new_guy", "name": "New", "zone": "main", "pos": [25, 25],
    }
    entity = empty_world.spawn_entity(entity_def)
    assert entity.id == "new_guy"
    assert "new_guy" in empty_world.entities


def test_spawn_entity_duplicate_id_raises(empty_world):
    entity_def = {
        "id": "dup", "name": "First", "zone": "main", "pos": [0, 0],
    }
    empty_world.spawn_entity(entity_def)

    dup_def = {
        "id": "dup", "name": "Second", "zone": "main", "pos": [10, 10],
    }
    with pytest.raises(ValueError, match="already exists"):
        empty_world.spawn_entity(dup_def)

    # Verify the original entity is untouched
    assert empty_world.entities["dup"].name == "First"


# ── despawn_entity ──

def test_despawn_entity_exists(minimal_world):
    assert minimal_world.despawn_entity("agent_1") is True
    assert "agent_1" not in minimal_world.entities


def test_despawn_entity_nonexistent(minimal_world):
    assert minimal_world.despawn_entity("nobody") is False


# ── update_entity ──

def test_update_entity_pos(minimal_world):
    minimal_world.update_entity("agent_1", {"pos": [30, 30]})
    assert minimal_world.entities["agent_1"].pos == [30, 30]


def test_update_entity_dotpath(minimal_world):
    minimal_world.update_entity("agent_1", {"agent.main_thread": "new goal"})
    al = minimal_world.entities["agent_1"].get("agent")
    assert al.main_thread == "new goal"


def test_update_entity_nonexistent(minimal_world):
    minimal_world.update_entity("ghost", {"pos": [0, 0]})
