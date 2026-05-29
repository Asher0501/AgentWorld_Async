"""Channel-driven context collection.

Each channel is a data source that formats its own fields into ctx dict.
loop.py calls channel.collect() once — no formatting, no judgment, no naming.
Channel definitions come from YAML; source classes handle the data extraction.
"""

import time


class ChannelCollector:
    """Collect ctx from YAML-defined channels, dispatching to source classes."""

    def __init__(self, channels_def: list[dict], labels: dict = None):
        self._channels = channels_def or []
        self._sources = {
            "agent_layer": AgentLayerSource(labels),
            "world":       WorldSource(),
            "drives":      DriveSource(),
            "sensory":     SensorySource(labels),
            "memory":      MemorySource(labels),
            "traits":      TraitsSource(),
            "delta_gate":  DeltaGateSource(),
        }

    def collect(self, ctx: dict, *, agent, al, world, sensory,
                cfg, delta_text, loader, **opts):
        for ch in self._channels:
            source_name = ch.get("source", "")
            fields = ch.get("fields", [])
            source = self._sources.get(source_name)
            if not source:
                continue
            data = source.collect(fields,
                                  agent=agent, al=al, world=world,
                                  sensory=sensory, cfg=cfg,
                                  loader=loader,
                                  delta_text=delta_text, **opts)
            ctx.update(data)
        return ctx


# ── Source implementations ──

class AgentLayerSource:
    """Collect agent identity, intent, and interaction tracking data."""

    def __init__(self, labels=None):
        self._labels = labels or {}

    def collect(self, fields: list[str], *, agent, al, **opts):
        result = {}
        for f in fields:
            if f == "personality":
                result[f] = agent.name + " — " + (al.personality or "")
            elif f == "name":
                result[f] = agent.name
            elif f == "main_thread":
                result[f] = al.main_thread or ""
            elif f == "last_intent":
                result[f] = al._last_intent or ""
            elif f == "last_target":
                result[f] = al._last_target_name or ""
            elif f == "conversation_text":
                result[f] = self._conversation_text(al)
            elif f == "item_narrative":
                result[f] = al._pending_narrative or ""
                al._pending_narrative = ""
        return result

    def _conversation_text(self, al) -> str:
        buf = al._conversation_buffer[-5:]
        if not buf:
            return ""
        lines = []
        for e in buf:
            ts = int(time.time() - e["ts"])
            lines.append(f"[{ts}s前] {e['speaker']}: {e['text']}")
        return "\n".join(lines)


class WorldSource:
    """Collect spatial context and gate information."""

    def collect(self, fields: list[str], *, agent, world, **opts):
        result = {}
        zone = world.zones.get(agent.zone, {})
        for f in fields:
            if f == "zone_name":
                result[f] = zone.get("name", "")
            elif f == "zone_width":
                result[f] = zone.get("width", 10)
            elif f == "zone_height":
                result[f] = zone.get("height", 10)
            elif f == "pos_x":
                result[f] = agent.pos[0]
            elif f == "pos_y":
                result[f] = agent.pos[1]
            elif f == "gate_text":
                result[f] = self._gates_for(agent, world)
        return result

    def _gates_for(self, agent, world) -> str:
        zone_entities = [e for e in world.entities.values() if e.zone == agent.zone]
        gates = []
        for e in zone_entities:
            inter = e.get("interaction") if e.has("interaction") else None
            if inter and inter.gate:
                dist = agent.distance_to(e)
                to_zone = world.zones.get(inter.gate.get("to_zone", ""), {}).get("name", "")
                gates.append(f"{e.name} ({dist}格) → {to_zone}")
        return "\n".join(gates) if gates else ""


class DriveSource:
    """Collect drive values and boundary references."""

    def collect(self, fields: list[str], *, al, **opts):
        result = {}
        for f in fields:
            if f == "drives_table":
                result[f] = al.drives.to_prompt()
            elif f == "drive_min":
                result[f] = 0
            elif f == "drive_max":
                result[f] = 100
        return result


class SensorySource:
    """Collect sensory channel renderings."""

    def __init__(self, labels=None):
        self._labels = labels or {}

    def collect(self, fields: list[str], *, sensory, **opts):
        result = {}
        if "sensory_text" in fields:
            sp = self._labels.get("sensory_prompts", {})
            parts = [t for ch, cfg in sp.items() if (t := sensory.to_prompt(ch, cfg))]
            result["sensory_text"] = "\n\n".join(parts)
        return result


class MemorySource:
    """Collect memory text."""

    def __init__(self, labels=None):
        self._labels = labels or {}

    def collect(self, fields: list[str], *, al, cfg, **opts):
        result = {}
        if "memory_text" in fields:
            count = getattr(cfg, "memory_prompt_count", 5)
            result["memory_text"] = al.memory.to_prompt_text(count, self._labels)
        return result


class TraitsSource:
    """Collect behavioral traits text."""

    def collect(self, fields: list[str], *, al, loader, **opts):
        result = {}
        if "traits_text" in fields:
            all_traits = loader.data.get("traits", {})
            parts = []
            for t in al.traits:
                if t in all_traits:
                    parts.append(all_traits[t]["template"])
            result["traits_text"] = "\n\n".join(parts)
        return result


class DeltaGateSource:
    """Collect delta gate change signal."""

    def collect(self, fields: list[str], *, delta_text, **opts):
        result = {}
        if "delta_text" in fields:
            result["delta_text"] = delta_text or ""
        return result
