"""Channel-driven context collection.

Each channel is a data source that formats its own fields into ctx dict.
loop.py calls channel.collect() once — no formatting, no judgment, no naming.

Principle 8: sources are auto-registered. To add a new source:
  1. Add a class with a `source_name` attribute to this module
  2. Add its class to _SOURCE_REGISTRY
  3. Add a channel entry in config/channels.yaml
The ChannelCollector._sources dict is built from _SOURCE_REGISTRY — zero code change in the collector.
"""

import time


class ChannelCollector:
    """Collect ctx from YAML-defined channels, dispatching to registered source classes."""

    def __init__(self, channels_def: list[dict], labels: dict = None,
                 graph: object = None):
        self._channels = channels_def or []
        self._sources = {}
        self._graph = graph
        for cls in _SOURCE_REGISTRY:
            src_name = getattr(cls, "source_name", "")
            if src_name:
                self._sources[src_name] = cls(labels=labels, graph=graph)

    def set_graph(self, graph):
        self._graph = graph
        for src_name, src in self._sources.items():
            if hasattr(src, '_graph'):
                src._graph = graph
        self._graph = graph
        for src_name, src in self._sources.items():
            if hasattr(src, '_graph'):
                src._graph = graph

    def _rebuild_sources(self, labels=None):
        for cls in _SOURCE_REGISTRY:
            src_name = getattr(cls, "source_name", "")
            if src_name:
                self._sources[src_name] = cls(labels=labels, graph=self._graph)

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
    source_name = "agent_layer"

    def __init__(self, labels=None, graph=None):
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
            elif f == "sensory_analysis_text":
                result[f] = al._sensory_analysis
            elif f == "quest_analysis_text":
                result[f] = al._quest_analysis
            elif f == "memory_analysis_text":
                result[f] = al._memory_analysis
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
    source_name = "world"

    def __init__(self, labels=None, graph=None):
        pass

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
    source_name = "drives"

    def __init__(self, labels=None, graph=None):
        pass

    def collect(self, fields: list[str], *, al, **opts):
        result = {}
        for f in fields:
            if f == "drives_table":
                result[f] = al.drives.to_prompt()
        return result


class SensorySource:
    source_name = "sensory"

    def __init__(self, labels=None, graph=None):
        self._labels = labels or {}

    def collect(self, fields: list[str], *, sensory, agent=None, **opts):
        result = {}
        if "sensory_text" in fields:
            sp = self._labels.get("sensory_prompts", {})
            observer_name = agent.name if agent else ""
            parts = [t for ch, cfg in sp.items() if (t := sensory.to_prompt(ch, cfg, observer_name))]
            result["sensory_text"] = "\n\n".join(parts)
        return result


class MemorySource:
    source_name = "memory"

    def __init__(self, labels=None, graph=None):
        self._labels = labels or {}

    def collect(self, fields: list[str], *, al, cfg, **opts):
        result = {}
        if "memory_text" in fields:
            count = getattr(cfg, "memory_prompt_count", 5)
            result["memory_text"] = al.memory.to_prompt_text(count, self._labels)
        return result


class TraitsSource:
    source_name = "traits"

    def __init__(self, labels=None, graph=None):
        pass

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
    source_name = "delta_gate"

    def __init__(self, labels=None, graph=None):
        pass

    def collect(self, fields: list[str], *, delta_text, **opts):
        result = {}
        if "delta_text" in fields:
            result["delta_text"] = delta_text or ""
        return result


class GraphSource:
    """Collect graph-layer data: inventory (npc→type_node edges)."""

    source_name = "graph"

    def __init__(self, labels=None, graph=None):
        self._graph = graph
        self._labels = labels or {}

    def collect(self, fields: list[str], *, agent, world, **opts):
        result = {}
        if "inventory_lines" in fields:
            result["inventory_lines"] = self._render_inventory(agent, world)
        if "tool_list" in fields:
            result["tool_list"] = self._render_tool_list(world)
        return result

    def _render_tool_list(self, world) -> str:
        mcp = getattr(world, "mcp", None)
        if not mcp:
            return ""
        abstract = mcp.layers.get("abstract")
        if not abstract:
            return ""
        lines = []
        for name, iface in sorted(abstract.interfaces.items()):
            lines.append(f"  - {name}: " + iface.to_prompt_line().split("    ", 1)[-1])
        return "\n".join(lines) if lines else ""

    def _render_inventory(self, agent, world) -> str:
        if not self._graph:
            return ""
        lines = []
        for (src, tgt), qty in self._graph.edges.items():
            if src == agent.id and qty > 0:
                tgt_node = world.entities.get(tgt)
                if tgt_node:
                    lines.append(f"{tgt_node.name} ×{int(qty)}")
        return "\n".join(lines) if lines else "空手"


# ── Source registry — add new source classes here ──
# Order matters: sources are instantiated in list order.
# Each source must accept (labels=None, graph=None) in __init__.

_SOURCE_REGISTRY = [
    AgentLayerSource,
    WorldSource,
    DriveSource,
    SensorySource,
    MemorySource,
    TraitsSource,
    DeltaGateSource,
    GraphSource,
]
