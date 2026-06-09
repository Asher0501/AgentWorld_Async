import yaml, os
import importlib

from core.clock import SimClock
from core.spatial_grid import SpatialGrid
from core.lifecycle import EntityLifecycle
from entity.entity import Entity
from layers.base import Layer
from agent.drives import DriveSystem
from agent.sensory_memory import SensoryMemory
from agent.memory import AgentMemory

_CFG_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config")


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def _import_class(dotted_path: str):
    parts = dotted_path.rsplit(".", 1)
    mod = importlib.import_module(parts[0])
    return getattr(mod, parts[1])


class World:
    def __init__(self, world_config: dict, systems: dict):
        self.config = world_config.get("world", {})
        self._world_cfg = world_config
        time_scale = self.config.get("time_scale", 60)
        self.clock = SimClock(
            self.config.get("start_time", "08:00"),
            time_scale,
        )

        self.zones: dict[str, dict] = {}
        self.entities: dict[str, Entity] = {}
        self.grids: dict[str, SpatialGrid] = {}

        self.lifecycle = EntityLifecycle(self)
        self._slot_groups = self._load_slot_groups()
        self._layer_registry = self._load_layer_registry()
        self._item_registry = self._load_yaml("item_registry.yaml")
        self._attr_cfg = self.config.get("simulation", {}).get("drive", {}).get("attributes", {})

        for zone_def in world_config.get("zones", []):
            self.zones[zone_def["id"]] = zone_def
            self.grids[zone_def["id"]] = SpatialGrid(
                zone_def["width"], zone_def["height"], cell_size=5
            )

        self._load_entities(world_config.get("entities", []))

        from core.graph import GraphEngine
        self.graph = GraphEngine(self, self._item_registry)
        self._load_npc_interfaces()
        self._init_abstract_layer()

    def _load_npc_interfaces(self):
        """Load world-bound physical interfaces and wire to agent layers."""
        path = os.path.join(_CFG_ROOT, "worlds", "witcher", "npc_interfaces.yaml")
        try:
            with open(path) as f:
                iface_cfg = yaml.safe_load(f)
        except FileNotFoundError:
            return
        # Build impl map: interface_name → callable
        impl_map = {}
        import worlds.witcher.npc_actions as actions
        for group in iface_cfg.values():
            if isinstance(group, list):
                for iface in group:
                    impl_map[iface["id"]] = getattr(actions, iface["impl"].split(".")[-1], None)
        # Wire to agent layers — each NPC gets all "通用" + role-specific interfaces
        for e in self.entities.values():
            if not e.has("agent"):
                continue
            al = e.get("agent")
            al.interfaces = {}
            for group_name, group in iface_cfg.items():
                if not isinstance(group, list):
                    continue
                for iface in group:
                    npcs = iface.get("npcs")
                    if npcs and e.name not in npcs:
                        continue
                    fn = impl_map.get(iface["id"])
                    if fn:
                        al.interfaces[iface["id"]] = fn

    def _init_abstract_layer(self):
        """Build type_nodes from item_registry, initial edges from holds, alias_registry."""
        # Create type_node for each item type
        for alias, cfg in self._item_registry.items():
            tid = f"type_{alias}"
            if tid not in self.entities:
                tn = Entity(id=tid, name=alias, zone="", pos=[0, 0])
                tn.type_ref = ""
                self.lifecycle.spawn(tn)

        # Build initial edges from NPC holds
        for e in self.entities.values():
            holds = getattr(e, '_holds', None)
            if not holds:
                continue
            for item_name, qty in holds.items():
                type_id = f"type_{item_name}"
                if type_id in self.entities:
                    self.graph.edges[(e.id, type_id)] = float(qty)

        # Build alias_registry
        from core.alias_registry import build_alias_registry
        self.alias_registry = build_alias_registry(self, self.graph, self._item_registry)

    def _load_layer_registry(self) -> dict:
        return self._load_yaml("layer_registry.yaml")

    def _load_yaml(self, filename: str) -> dict:
        path = os.path.join(_CFG_ROOT, filename)
        try:
            with open(path) as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}

    def _load_slot_groups(self) -> dict:
        path = os.path.join(_CFG_ROOT, "slot_groups.yaml")
        with open(path) as f:
            return yaml.safe_load(f)

    def _resolve_group_mask(self, layer_name: str, group_id: str) -> dict:
        """Resolve a group row from slot_groups.yaml into a {slot: 0/1} mask."""
        groups_cfg = self._slot_groups.get(layer_name, {})
        columns = groups_cfg.get("columns", [])
        groups = groups_cfg.get("groups", {})
        row = groups.get(group_id, groups.get("default", [1] * len(columns)))
        return {col: int(row[i]) for i, col in enumerate(columns)}

    def _resolve_slot_mask(self, ent_def: dict, eid: str, traits_matrix: dict, default_traits: list) -> dict:
        """Build slot mask from dimensions defined in slot_groups.yaml."""
        dims = self._slot_groups.get("dimensions", [])
        if not dims:
            # Fallback: hardcoded legacy dimensions
            world_group = self._world_cfg.get("world-group", "default")
            world_mask = self._resolve_group_mask("world", world_group)
            contract_mask = self._resolve_group_mask("contract", "default")
            npc_group = ent_def.get("npc-group", "default")
            npc_mask = self._resolve_group_mask("npc", npc_group)
            return {**contract_mask, **world_mask, **npc_mask}

        slot_mask = {}
        for dim in dims:
            name = dim["name"]
            source = dim.get("source", "static")
            if source == "static":
                group = dim.get("default", "default")
            else:
                group = self._world_cfg.get(source) if source in ("world-group",) else ent_def.get(source)
                if not group:
                    group = dim.get("default", "default")
            mask = self._resolve_group_mask(name, group)
            slot_mask.update(mask)
        return slot_mask

    def _load_entities(self, entity_defs: list[dict]) -> None:
        traits_matrix = self._world_cfg.get("traits", {})
        default_traits = traits_matrix.get("default", [])

        for ent_def in entity_defs:
            eid = ent_def["id"]
            entity = Entity(
                id=ent_def["id"],
                name=ent_def["name"],
                zone=ent_def["zone"],
                pos=list(ent_def.get("pos", [0, 0])),
                describe=ent_def.get("description", ent_def.get("describe", "")),
            )

            # ── Generic layer construction (Principle 8: YAML-driven variants) ──
            # Each layer type defined in layer_registry.yaml is constructed via
            # class lookup + deep-merge defaults + YAML override.
            # InteractionLayer extra fields (radius, qty, ops) are passed as kwargs.
            for layer_name, layer_reg in self._layer_registry.items():
                if layer_name not in ent_def:
                    continue
                layer_cfg = ent_def[layer_name]
                klass = _import_class(layer_reg["class"])
                defaults = dict(layer_reg.get("defaults", {}))
                merged = _deep_merge(defaults, self._extract_dataclass_fields(layer_cfg, klass))
                entity.layers[layer_name] = klass(**merged)

            # ── Interaction layer extra fields ──
            if "interaction" in ent_def and entity.has("interaction"):
                inter_cfg = ent_def["interaction"]
                il = entity.get("interaction")
                il.gate = inter_cfg.get("gate")
                il.hidden = inter_cfg.get("hidden", {})
                il.private_attrs = inter_cfg.get("private_attrs", {})
                il.readonly = inter_cfg.get("readonly", False)
                il.filepath = inter_cfg.get("filepath", "")

            # ── Agent-specific wiring ──
            if "agent" in ent_def:
                ag = ent_def["agent"]
                agent_traits = ag.get("traits") or traits_matrix.get(eid, default_traits)
                slot_mask = self._resolve_slot_mask(ag, eid, traits_matrix, default_traits)

                al = entity.get("agent")
                al.slot_mask = slot_mask
                al.traits = agent_traits

                if entity.has("interaction"):
                    al.drives = DriveSystem(
                        attrs=entity.get("interaction").private_attrs,
                    )
                al.sensory = SensoryMemory()
                al.memory = AgentMemory()

                # Holds data for abstract layer edges (phase 2 init)
                holds = ent_def.get("holds", None)
                if holds:
                    entity._holds = holds

                aud_reg = self._layer_registry.get("auditory", {})
                aud_klass = _import_class(aud_reg["class"]) if aud_reg.get("class") else Layer
                aud_defaults = dict(aud_reg.get("defaults", {}))
                entity.layers["auditory"] = aud_klass(
                    audible_radius=ag.get("hearing_radius", 15),
                    properties={"sound": ""})

            # ── Generic layers: unknown layer type → base Layer ──
            for layer_name, layer_cfg in ent_def.get("layers", {}).items():
                if layer_name in entity.layers:
                    continue
                props = layer_cfg.get("properties", {})
                radius = layer_cfg.get("observable_radius", 5)
                entity.layers[layer_name] = Layer(
                    properties=props, observable_radius=radius)

            self.lifecycle.spawn(entity)

    @staticmethod
    def _extract_dataclass_fields(layer_cfg: dict, klass) -> dict:
        """Extract only the YAML keys that map to the dataclass's __init__ params."""
        import inspect
        params = inspect.signature(klass).parameters.keys() if hasattr(klass, '__dataclass_fields__') else layer_cfg.keys()
        return {k: v for k, v in layer_cfg.items()
                if k in params or k in ("properties", "sprite")}

    def get_nearby_ids(self, zone_id: str, pos: list[int], radius: int) -> set[str]:
        grid = self.grids.get(zone_id)
        if grid:
            return grid.query_ids(pos, radius)
        return {eid for eid, e in self.entities.items()
                if e.zone == zone_id}

    def notify_moved(self, entity_id: str, old_pos: list[int], new_pos: list[int],
                     zone_id: str) -> None:
        grid = self.grids.get(zone_id)
        if grid:
            grid.move(entity_id, old_pos, new_pos)

    def update_entity(self, entity_id: str, updates: dict) -> None:
        """Apply dotted-path updates to entity properties. Blind execution — no schema."""
        entity = self.entities.get(entity_id)
        if not entity:
            return
        for path, value in updates.items():
            parts = path.split(".")
            target = entity
            for p in parts[:-1]:
                if hasattr(target, 'get'):
                    target = target.get(p)
                else:
                    target = getattr(target, p, None)
                if target is None:
                    break
            else:
                if hasattr(target, '__setitem__'):
                    target[parts[-1]] = value
                else:
                    setattr(target, parts[-1], value)

    def spawn_entity(self, entity_def: dict) -> Entity:
        """Create and spawn an entity from a dict at runtime. Same format as world.yaml."""
        saved = self.entities.copy()
        self._load_entities([entity_def])
        for eid in self.entities:
            if eid not in saved:
                return self.entities[eid]
        raise RuntimeError(f"Failed to spawn entity: {entity_def.get('id', '?')}")

    def despawn_entity(self, entity_id: str) -> bool:
        """Remove an entity from the world at runtime."""
        return self.lifecycle.despawn(entity_id)
