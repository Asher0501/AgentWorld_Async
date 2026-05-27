"""Config validation tests — YAML loading and structure checks."""
import os
import yaml
import pytest


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_world_friends_config_loads():
    from cli.config import load_config
    cfg = load_config(os.path.join(ROOT, "config", "world_friends.yaml"))
    assert cfg["world"]["world"]["name"] == "老友记 — Central Perk"
    assert len(cfg["world"]["entities"]) == 21
    assert "llm_clients" in cfg


def test_slot_groups_structure():
    with open(os.path.join(ROOT, "config", "slot_groups.yaml")) as f:
        sg = yaml.safe_load(f)
    assert "contract" in sg
    assert "world" in sg
    assert "npc" in sg
    assert sg["npc"]["groups"]["default"] == [1, 1, 1, 1, 1, 1, 1, 1]


def test_director_permissions_structure():
    with open(os.path.join(ROOT, "config", "director_permissions.yaml")) as f:
        dp = yaml.safe_load(f)
    assert dp["groups"]["controller"] == 1
    assert dp["groups"]["moderator"] == 2
    assert dp["groups"]["admin"] == 3
    assert dp["fields"]["agent.memory"] == 2
    assert dp["fields"]["agent.pos"] == 3
