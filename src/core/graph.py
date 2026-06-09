"""GraphEngine — 6 primitives. All writes go through these.

Edge model: (src, tgt, qty), untyped. Semantics from node types.
primitives: delta, spawn, despawn, relocate, add_node, remove_node
"""

import uuid
from entity.entity import Entity


class GraphEngine:
    def __init__(self, world, item_registry_cfg: dict):
        self._world = world
        self._item_registry = item_registry_cfg
        self.edges: dict[tuple[str, str], float] = {}
        # Public index of primitives — accessible by name for engine routing
        self.primitives = {
            "delta":       self.delta,
            "spawn":       self.spawn,
            "despawn":     self.despawn,
            "relocate":    self.relocate,
            "add_node":    self.add_node,
            "remove_node": self.remove_node,
        }

    # ═══════════ primitives ═══════════

    def delta(self, *, src=None, tgt=None, entity=None, attr=None, value=None, qty=None):
        """Universal ± on edges or entity attributes.
        Edge form: delta(src=..., tgt=..., qty=N)
        Attr form: delta(entity=..., attr=..., value=N)
        """
        # Edge delta
        if src is not None and tgt is not None:
            v = qty if qty is not None else value
            if v is None:
                return False
            s = src.id if isinstance(src, Entity) else src
            t = tgt.id if isinstance(tgt, Entity) else tgt
            key = (s, t)
            cur = self.edges.get(key, 0)
            nxt = cur + float(v)
            if nxt < 0:
                return False
            self.edges[key] = nxt
            return True
        # Attr delta
        if entity is not None and attr is not None:
            v = qty if qty is not None else value
            if v is None:
                return False
            ent = self._world.entities.get(entity.id) if isinstance(entity, Entity) else self._world.entities.get(entity)
            if not ent:
                return False
            inter = ent.get("interaction") if ent.has("interaction") else None
            if not inter:
                return False
            cur = float(inter.private_attrs.get(attr, 0))
            inter.private_attrs[attr] = cur + float(v)
            return True
        return False

    def spawn(self, *, pos, zone, type_ref, visual_look, r=1):
        """Entity appears in space. Reuses existing entity at same pos+zone+type_ref."""
        # Reuse check
        for e in self._world.entities.values():
            if e.zone == zone and e.pos == pos and getattr(e, "type_ref", "") == type_ref:
                return e  # Already exists — reuse
        # New entity
        eid = f"pile_{uuid.uuid4().hex[:6]}"
        ent = Entity(id=eid, name=visual_look, zone=zone, pos=list(pos))
        ent.type_ref = type_ref
        # Visual layer
        if visual_look:
            from layers.visual import VisualLayer
            ent.layers["visual"] = VisualLayer(
                visible_radius=r,
                properties={"look": visual_look},
            )
            # Alias registration
            reg = getattr(self._world, "alias_registry", None)
            if reg is not None and visual_look not in reg:
                reg[visual_look] = ent.id
        # Interaction layer for sensory/merge targeting
        from layers.interaction import InteractionLayer
        ent.layers["interaction"] = InteractionLayer(
            interaction_radius=1,
            properties={"description": visual_look},
        )
        self._world.lifecycle.spawn(ent)
        return ent

    def despawn(self, *, entity):
        """Entity disappears from space. Cleans alias."""
        eid = entity.id if isinstance(entity, Entity) else entity
        ent = self._world.entities.get(eid)
        # Alias cleanup
        reg = getattr(self._world, "alias_registry", None)
        if reg is not None and ent and ent.has("visual"):
            look = ent.get("visual").properties.get("look", "")
            if look and reg.get(look) == eid:
                del reg[look]
        return self._world.lifecycle.despawn(eid)

    def relocate(self, *, entity, pos):
        """Entity changes position."""
        e = self._world.entities.get(entity.id) if isinstance(entity, Entity) else self._world.entities.get(entity)
        if e:
            e.move_to(list(pos))
            return True
        return False

    def add_node(self, *, node_id):
        """Abstract layer: node enters edge system. Idempotent."""
        if node_id in self._world.entities:
            return True
        # Placeholder entity for pure abstract node
        ent = Entity(id=node_id, name=node_id, zone="", pos=[0, 0])
        self._world.lifecycle.spawn(ent)
        return True

    def remove_node(self, *, node_id):
        """Abstract layer: node leaves edge system. Cleans incident edges."""
        eid = node_id.id if isinstance(node_id, Entity) else node_id
        to_del = [k for k in self.edges if k[0] == eid or k[1] == eid]
        for k in to_del:
            del self.edges[k]
        return self._world.lifecycle.despawn(eid)
