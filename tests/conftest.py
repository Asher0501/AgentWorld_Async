"""Shared test fixtures. No filesystem reads, no LLM calls."""
import sys, os
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))


@pytest.fixture
def minimal_world_cfg():
    """Inline world config: 2 agents, 1 zone. No YAML file required."""
    return {
        "world": {"name": "test", "start_time": "08:00", "time_scale": 60},
        "zones": [{"id": "test_zone", "width": 100, "height": 100}],
        "entities": [
            {
                "id": "agent_1", "name": "Alice", "zone": "test_zone", "pos": [10, 10],
                "agent": {"autonomous": True, "personality": "friendly", "template": "npc"},
                "interaction": {"private_attrs": {"hunger": 50, "energy": 80}},
                "auditory": {"properties": {"current_speech": "", "speech_ts": 0}},
            },
            {
                "id": "agent_2", "name": "Bob", "zone": "test_zone", "pos": [20, 20],
                "agent": {"autonomous": True, "personality": "tired", "template": "npc"},
                "interaction": {"private_attrs": {"hunger": 30, "energy": 40}},
                "auditory": {"properties": {"current_speech": "", "speech_ts": 0}},
            },
        ],
    }


@pytest.fixture
def minimal_world(minimal_world_cfg):
    """Constructed World from inline config. LLM client is a stub — never called."""
    from core.world import World
    from systems.sensory import SensorySystem
    from systems.interaction import InteractionSystem
    from systems.decay import DecaySystem

    class _StubLLM:
        def __init__(self): pass
        async def chat(self, **kw): return "{}"

    world = World(minimal_world_cfg, {
        "sensory": SensorySystem(),
        "interaction": InteractionSystem(_StubLLM(), None),
        "decay": DecaySystem(),
    })
    return world


@pytest.fixture
def empty_world():
    """World with no entities — clean slate for spawn/despawn tests."""
    from core.world import World
    from systems.sensory import SensorySystem
    from systems.interaction import InteractionSystem
    from systems.decay import DecaySystem

    class _StubLLM:
        def __init__(self): pass
        async def chat(self, **kw): return "{}"

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
