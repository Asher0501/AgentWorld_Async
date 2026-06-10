"""GraphEngine — 7 primitives. All writes go through these.

Edge model: (src, tgt, qty), untyped. Semantics from node types.
Naming: {layer}_{name} — spatial_spawn, abs_holder_transfer, etc.
"""

import uuid
from entity.entity import Entity


class GraphEngine:
    def __init__(self, world, item_registry_cfg: dict):
        self._world = world
        self._item_registry = item_registry_cfg
        self.edges: dict[tuple[str, str], float] = {}
        self.primitives = {
            "abs_holder_transfer":  self.abs_holder_transfer,
            "abs_attr_modify":      self.abs_attr_modify,
            "spatial_spawn":        self.spatial_spawn,
            "spatial_despawn":      self.spatial_despawn,
            "spatial_relocate":     self.spatial_relocate,
            "abs_node_add":         self.abs_node_add,
            "abs_node_remove":      self.abs_node_remove,
        }

    # ═══════════ primitives ═══════════

    def abs_holder_transfer(self, *, src, tgt, qty, caller=None):
        """Abstract holder layer: edge quantity transfer.
        If caller is provided, verifies caller owns the source edge."""
        s = src.id if isinstance(src, Entity) else src
        if caller is not None and s and not self._is_zone(s):
            caller_id = caller.id if isinstance(caller, Entity) else caller
            if caller_id != s:
                return False
        t = tgt.id if isinstance(tgt, Entity) else tgt
        key = (s, t)
        cur = self.edges.get(key, 0)
        nxt = cur + float(qty)
        if nxt < 0:
            return False
        self.edges[key] = nxt
        return True

    def _is_zone(self, entity_id: str) -> bool:
        zones = getattr(self._world, "zones", {})
        return entity_id in zones

    def abs_attr_modify(self, *, entity, attr, value, caller=None):
        """Abstract attribute layer: entity attribute modification."""
        ent = self._world.entities.get(entity.id) if isinstance(entity, Entity) else self._world.entities.get(entity)
        if not ent and isinstance(entity, str):
            reg = getattr(self._world, "alias_registry", {})
            eid = reg.get(entity)
            if eid:
                ent = self._world.entities.get(eid)
        if not ent:
            return False
        inter = ent.get("interaction") if ent.has("interaction") else None
        if not inter:
            return False
        cur = float(inter.private_attrs.get(attr, 0))
        inter.private_attrs[attr] = cur + float(value)
        return True

    def spatial_spawn(self, *, pos, zone, type_ref, visual_look, r=1):
        """Spatial layer: entity appears in space."""
        eid = f"pile_{uuid.uuid4().hex[:6]}"
        ent = Entity(id=eid, name=visual_look, zone=zone, pos=list(pos))
        ent.type_ref = type_ref
        return self._world._on_entity_spawned(ent, visual_look=visual_look, r=r)

    def spatial_despawn(self, *, entity):
        """Spatial layer: entity disappears from space."""
        eid = entity.id if isinstance(entity, Entity) else entity
        self._world._on_entity_despawned(eid)
        return self._world.lifecycle.despawn(eid)

    def spatial_relocate(self, *, entity, pos):
        """Spatial layer: entity changes position."""
        e = self._world.entities.get(entity.id) if isinstance(entity, Entity) else self._world.entities.get(entity)
        if e:
            e.move_to(list(pos))
            return True
        return False

    def abs_node_add(self, *, node_id):
        """Abstract layer: node enters edge system. Idempotent."""
        if node_id in self._world.entities:
            return True
        ent = Entity(id=node_id, name=node_id, zone="", pos=[0, 0])
        self._world.lifecycle.spawn(ent)
        return True

    def abs_node_remove(self, *, node_id):
        """Abstract layer: node leaves edge system. Cleans incident edges."""
        eid = node_id.id if isinstance(node_id, Entity) else node_id
        to_del = [k for k in self.edges if k[0] == eid or k[1] == eid]
        for k in to_del:
            del self.edges[k]
        return self._world.lifecycle.despawn(eid)
