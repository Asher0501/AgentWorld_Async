"""EntityLifecycle — 统一实体生命周期管理。"""


class EntityLifecycle:

    def __init__(self, world):
        self.world = world

    def spawn(self, entity) -> None:
        w = self.world
        if entity.id in w.entities:
            raise ValueError(f"Entity ID '{entity.id}' already exists in world")
        w.entities[entity.id] = entity
        entity._world = w
        if entity.zone in w.grids:
            w.grids[entity.zone].insert(entity.id, entity.pos)

    def despawn(self, entity_id: str) -> bool:
        w = self.world
        entity = w.entities.pop(entity_id, None)
        if not entity:
            return False
        if entity.zone in w.grids:
            w.grids[entity.zone].remove(entity_id, entity.pos)
        return True

    def transfer_zone(self, entity, new_zone: str, new_pos: list[int]) -> None:
        """Move entity between zones. Clears sensory channels so stale visual/auditory
        data from the old zone doesn't persist. Conversation buffer (max 8 entries) is
        intentionally preserved — like a human remembering a conversation after leaving
        the room. It naturally ages out via the FIFO cap."""
        old_zone = entity.zone
        old_pos = list(entity.pos)

        if old_zone in self.world.grids:
            self.world.grids[old_zone].remove(entity.id, old_pos)

        entity.zone = new_zone
        entity.pos = new_pos

        if new_zone in self.world.grids:
            self.world.grids[new_zone].insert(entity.id, new_pos)

        if entity.has("agent"):
            ag = entity.get("agent")
            if ag.sensory:
                ag.sensory.clear()
