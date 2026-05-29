"""Director — controlled mode for NPC agents.

Freeze/unfreeze world, take/release NPC control with per-field permission levels,
snap sensory state, inject external decisions, blind-write agent fields.
All controlled-mode semantics in one place.
"""
import os, yaml

_CFG_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config")


class Director:
    def __init__(self, world):
        self.world = world
        self.frozen = False
        self._controlled: dict[str, int] = {}  # agent_id → permission level
        self._orders: dict[str, dict] = {}
        self._permissions = self._load_permissions()

    def _load_permissions(self) -> dict:
        path = os.path.join(_CFG_ROOT, "director_permissions.yaml")
        with open(path) as f:
            return yaml.safe_load(f)

    def freeze(self):
        """Pause the world. All NPC loops sleep at Phase 1."""
        self.frozen = True

    def unfreeze(self):
        """Resume the world. Pending orders begin executing."""
        self.frozen = False

    def take(self, agent_id: str, level: int = 1):
        """Take control of an NPC at given permission level.
        Levels: 0=observer 1=controller 2=moderator 3=admin 4=super.
        """
        self._controlled[agent_id] = level

    def release(self, agent_id: str):
        """Return an NPC to autonomous mode."""
        self._controlled.pop(agent_id, None)
        self._orders.pop(agent_id, None)

    def is_controlled(self, agent_id: str) -> bool:
        return agent_id in self._controlled

    def order(self, agent_id: str, decision: dict):
        """Inject a decision for a controlled NPC.
        The NPC will execute it on its next Phase 3.
        """
        self._orders[agent_id] = decision

    def pending(self, agent_id: str) -> dict | None:
        """Pop and return the pending order, or None."""
        return self._orders.pop(agent_id, None)

    def snap(self, agent_id: str) -> dict:
        """Return what an NPC currently perceives.
        Used by the operator to decide what to order.
        """
        agent = self.world.entities.get(agent_id)
        if not agent:
            return {}
        al = agent.get("agent")
        return {
            "name": agent.name,
            "zone": agent.zone,
            "pos": agent.pos,
            "drives": dict(al.drives.attrs) if al and al.drives else {},
            "memory": [e["text"] for e in al.memory.recent(5)] if al and al.memory else [],
            "sensory": al.sensory.channels if al and al.sensory else {},
            "main_thread": al.main_thread if al else "",
            "controlled": self.is_controlled(agent_id),
            "level": self._controlled.get(agent_id, -1),
        }

    # ══════ Field write ══════

    def _resolve_required(self, path: str) -> int:
        fields = self._permissions.get("fields", {})
        if path in fields:
            return fields[path]
        for pattern, level in fields.items():
            if pattern.endswith(".*") and path.startswith(pattern[:-2]):
                return level
        return 4  # super — default fallback

    def _check_level(self, agent_id: str, path: str):
        current = self._controlled.get(agent_id, -1)
        required = self._resolve_required(path)
        if current < required:
            raise PermissionError(
                f"{agent_id}: field '{path}' requires level ≥{required}, have {current}")

    def set(self, agent_id: str, path: str, value):
        """Blind-write any agent field by dotted-path. Permission-checked."""
        self._check_level(agent_id, path)
        entity = self.world.entities.get(agent_id)
        if not entity:
            return
        parts = path.split(".")
        target = entity
        for p in parts[:-1]:
            if hasattr(target, 'get'):
                target = target.get(p)
            else:
                target = getattr(target, p, None)
            if target is None:
                return
        if hasattr(target, '__setitem__'):
            target[parts[-1]] = value
        else:
            setattr(target, parts[-1], value)

    def memorize(self, agent_id: str, text: str):
        """Write to agent's memory. Convenience for set('agent.memory', text)."""
        self._check_level(agent_id, "agent.memory")
        al = self.world.entities[agent_id].get("agent")
        if al and al.memory:
            al.memory.record(text)
