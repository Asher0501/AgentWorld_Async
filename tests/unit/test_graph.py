"""Unit tests for GraphEngine 7 primitives."""
import pytest

_CFG = None


class FakeWorld:
    entities = {}
    grids = {}
    lifecycle = None
    alias_registry = {}
    _layer_registry = {"item": {"layers": ["visual", "interaction"], "reuse_key": ["zone", "pos", "type_ref"]}}

    def __init__(self):
        from core.lifecycle import EntityLifecycle
        from core.spatial_grid import SpatialGrid
        self.lifecycle = EntityLifecycle(self)
        self.grids["test"] = SpatialGrid(60, 40)

    def _on_entity_spawned(self, entity, *, visual_look="", r=1):
        for e in self.entities.values():
            if e.zone == entity.zone and e.pos == entity.pos and getattr(e, "type_ref", "") == entity.type_ref:
                return e
        if visual_look:
            from layers.visual import VisualLayer
            entity.layers["visual"] = VisualLayer(visible_radius=r, properties={"look": visual_look})
            if visual_look not in self.alias_registry:
                self.alias_registry[visual_look] = entity.id
        from layers.interaction import InteractionLayer
        entity.layers["interaction"] = InteractionLayer(interaction_radius=1, properties={"description": visual_look})
        self.lifecycle.spawn(entity)
        return entity

    def _on_entity_despawned(self, eid):
        ent = self.entities.get(eid)
        if ent and ent.has("visual"):
            look = ent.get("visual").properties.get("look", "")
            if look and self.alias_registry.get(look) == eid:
                del self.alias_registry[look]

    def spawn_entity(self, defn):
        from entity.entity import Entity
        e = Entity(id=defn.get("id", "tmp"), name=defn.get("name", ""),
                   zone=defn.get("zone", "test"), pos=list(defn.get("pos", [0, 0])))
        self.lifecycle.spawn(e)
        return e

    def notify_moved(self, *a, **kw):
        pass


@pytest.fixture
def world():
    return FakeWorld()


@pytest.fixture
def graph(world):
    from core.graph import GraphEngine
    return GraphEngine(world, {})


@pytest.fixture
def npc(world):
    from entity.entity import Entity
    from layers.agent import AgentLayer
    from layers.interaction import InteractionLayer
    e = Entity(id="geralt", name="杰洛特", zone="test", pos=[30, 25])
    if "geralt" not in world.entities:
        e.layers["agent"] = AgentLayer(autonomous=True)
        e.layers["interaction"] = InteractionLayer(private_attrs={"hunger": 50, "thirst": 60})
        world.lifecycle.spawn(e)
    return world.entities["geralt"]


class TestTransfer:
    def test_transfer_positive(self, graph):
        graph.edges[("geralt", "gold")] = 10
        assert graph.abs_holder_transfer(src="geralt", tgt="gold", qty=5)
        assert graph.edges[("geralt", "gold")] == 15

    def test_transfer_negative(self, graph):
        graph.edges[("geralt", "gold")] = 10
        assert not graph.abs_holder_transfer(src="geralt", tgt="gold", qty=-15)

    def test_transfer_entity(self, graph, npc):
        graph.edges[("geralt", "gold")] = 10
        assert graph.abs_holder_transfer(src=npc, tgt="gold", qty=-5)
        assert graph.edges[("geralt", "gold")] == 5


class TestModify:
    def test_modify(self, graph, npc):
        assert graph.abs_attr_modify(entity=npc, attr="hunger", value=-10)
        assert npc.get("interaction").private_attrs["hunger"] == 40.0

    def test_modify_nonexistent_entity(self, graph):
        assert not graph.abs_attr_modify(entity="nonexistent", attr="x", value=1)


class TestSpawn:
    def test_spawn_creates_entity(self, graph):
        e = graph.spatial_spawn(pos=[30, 25], zone="test", type_ref="gold",
                        visual_look="杰洛特手中的金币", r=1)
        assert e is not None
        assert e.pos == [30, 25]
        assert e.type_ref == "gold"

    def test_spawn_reuses_entity(self, graph):
        e1 = graph.spatial_spawn(pos=[30, 25], zone="test", type_ref="gold", visual_look="first")
        e2 = graph.spatial_spawn(pos=[30, 25], zone="test", type_ref="gold", visual_look="second")
        assert e1.id == e2.id

    def test_spawn_registers_alias(self, graph, world):
        graph.spatial_spawn(pos=[30, 25], zone="test", type_ref="gold", visual_look="杰洛特手中的金币")
        assert "杰洛特手中的金币" in world.alias_registry


class TestDespawn:
    def test_despawn_removes_entity(self, graph):
        e = graph.spatial_spawn(pos=[30, 25], zone="test", type_ref="gold", visual_look="test_coin")
        eid = e.id
        assert graph.spatial_despawn(entity=e)
        assert eid not in graph._world.entities

    def test_despawn_cleans_alias(self, graph, world):
        e = graph.spatial_spawn(pos=[30, 25], zone="test", type_ref="gold", visual_look="test_coin_2")
        graph.spatial_despawn(entity=e)
        assert "test_coin_2" not in world.alias_registry


class TestRelocate:
    def test_relocate(self, graph, npc):
        assert graph.spatial_relocate(entity=npc, pos=[40, 30])
        assert npc.pos == [40, 30]


class TestAddRemoveNode:
    def test_add_node(self, graph):
        assert graph.abs_node_add(node_id="abstract_x")
        assert "abstract_x" in graph._world.entities

    def test_remove_node_cleans_edges(self, graph, world):
        graph.abs_node_add(node_id="node_x")
        world.entities["node_x"].id = "node_x"
        graph.edges[("node_x", "gold")] = 5
        graph.edges[("village", "node_x")] = 3
        assert graph.abs_node_remove(node_id="node_x")
        assert ("node_x", "gold") not in graph.edges
