"""Basic validation tests — no LLM calls, no API keys needed."""
import sys, os
import pytest

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(base, "src"))


def test_validate_config():
    from cli.config import load_config
    cfg = load_config(os.path.join(base, "config", "world_friends.yaml"))
    assert cfg["world"]["world"]["name"] == "老友记 — Central Perk"
    assert len(cfg["world"]["entities"]) == 21
    assert "llm_clients" in cfg


def test_spawn_world():
    from cli.config import load_config
    from cli.world_setup import spawn_world, get_autonomous_agents
    cfg = load_config(os.path.join(base, "config", "world_friends.yaml"))
    world, brain, systems = spawn_world(cfg)
    agents = get_autonomous_agents(world)
    assert len(agents) == 7


def test_slot_groups_loaded():
    import yaml
    with open(os.path.join(base, "config", "slot_groups.yaml")) as f:
        sg = yaml.safe_load(f)
    assert "contract" in sg
    assert "world" in sg
    assert "npc" in sg
    assert sg["npc"]["groups"]["default"] == [1, 1, 1, 1, 1, 1, 1, 1]


def test_event_bus():
    from event_bus import EventBus
    eb = EventBus(history_size=10)
    eb.emit({"agent": "test", "action_text": "hello"})
    assert len(eb._history) == 1
    assert eb._history[0]["agent"] == "test"


def test_director():
    from core.director import Director
    d = Director.__new__(Director)
    d.world = None
    d.frozen = False
    d._controlled = set()
    d._orders = {}
    assert not d.frozen
    d.freeze()
    assert d.frozen
    d.unfreeze()
    assert not d.frozen
