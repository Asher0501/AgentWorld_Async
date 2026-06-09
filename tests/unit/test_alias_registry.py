"""Unit tests for alias_registry."""
import pytest
from core.alias_registry import build_alias_registry


class FakeGraph:
    edges = {}


class FakeWorld:
    entities = {}


@pytest.fixture
def world_with_items():
    from entity.entity import Entity
    from layers.visual import VisualLayer

    w = FakeWorld()

    # Type node
    gold = Entity(id="type_金币", name="金币", zone="", pos=[0, 0])
    w.entities["type_金币"] = gold

    herb = Entity(id="type_草药", name="草药", zone="", pos=[0, 0])
    w.entities["type_草药"] = herb

    # Ground pile with visual_look
    pile = Entity(id="gp_1", name="金币堆", zone="village", pos=[38, 16])
    pile.layers["visual"] = VisualLayer(visible_radius=5,
                                         properties={"look": "吧台角落的一小堆金币"})
    w.entities["gp_1"] = pile

    return w


class TestAliasRegistry:
    def test_item_registry_aliases(self, world_with_items):
        item_cfg = {"金币": {}, "草药": {}}
        reg = build_alias_registry(world_with_items, FakeGraph(), item_cfg)
        assert reg["金币"] == "type_金币"
        assert reg["草药"] == "type_草药"

    def test_spatial_visual_look(self, world_with_items):
        reg = build_alias_registry(world_with_items, FakeGraph(), {})
        assert reg["吧台角落的一小堆金币"] == "gp_1"

    def test_entity_name_fallback(self, world_with_items):
        reg = build_alias_registry(world_with_items, FakeGraph(), {})
        assert reg["金币堆"] == "gp_1"

    def test_abstract_overrides_name(self, world_with_items):
        """When type_node exists for same name, abstract wins."""
        # Add type_node that matches pile name
        from entity.entity import Entity
        tn = Entity(id="type_金币堆", name="金币堆", zone="", pos=[0, 0])
        world_with_items.entities["type_金币堆"] = tn
        item_cfg = {"金币堆": {}}
        reg = build_alias_registry(world_with_items, FakeGraph(), item_cfg)
        assert reg["金币堆"] == "type_金币堆"
