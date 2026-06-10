"""MCP Engine — world-agnostic interface routing.

Layers register named Interfaces. LLM outputs tool calls. Engine routes to handlers.
Zero domain vocabulary. Zero awareness of what interfaces do.

Usage:
    mcp = MCPEngine()
    mcp.register_layer("physical", Layer.from_yaml("npc_interfaces.yaml", actions))
    mcp.register_layer("abstract", Layer.from_primitives(graph.primitives, DEFS))
    result = mcp.route("physical", call, ctx=ctx)
"""

import yaml
from dataclasses import dataclass, field


@dataclass
class ParamDef:
    name: str
    type: str = "str"   # "alias" | "int" | "str"
    desc: str = ""
    required: bool = True


@dataclass
class Interface:
    name: str
    desc: str = ""
    handler: object = None   # callable(agent, params, world) or callable(**params)
    params: list[ParamDef] = field(default_factory=list)

    def validate(self, call_params: dict) -> list[str]:
        errors = []
        for p in self.params:
            if p.required and p.name not in call_params:
                errors.append(f"缺少必需参数 '{p.name}' ({p.desc})")
        return errors

    def to_prompt_line(self) -> str:
        params_str = ", ".join(
            f"{p.name}:{p.type}" + ("" if p.required else "?")
            for p in self.params
        )
        return f"  - {self.name}: {{{params_str}}}    {self.desc}"


@dataclass
class Layer:
    """Named collection of Interfaces."""
    name: str
    interfaces: dict[str, Interface] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str, impl_module) -> "Layer":
        with open(path) as f:
            cfg = yaml.safe_load(f)
        interfaces = {}
        for group in cfg.values():
            if not isinstance(group, list):
                continue
            for iface_def in group:
                name = iface_def["id"]
                impl_name = iface_def["impl"].split(".")[-1]
                handler = getattr(impl_module, impl_name, None)
                params = [ParamDef(**p) for p in iface_def.get("params", [])]
                interfaces[name] = Interface(
                    name=name,
                    desc=iface_def.get("desc", ""),
                    handler=handler,
                    params=params,
                )
        return cls(name="physical", interfaces=interfaces)

    @classmethod
    def from_primitives(cls, primitives: dict, definitions: dict) -> "Layer":
        interfaces = {}
        for name, handler in primitives.items():
            iface_def = definitions.get(name, {})
            if iface_def.get("expose_to_llm") is False:
                continue
            interfaces[name] = Interface(
                name=name,
                desc=iface_def.get("desc", ""),
                handler=handler,
                params=[ParamDef(**p) for p in iface_def.get("params", [])],
            )
        return cls(name="abstract", interfaces=interfaces)

    def subset(self, keys: set[str]) -> dict[str, Interface]:
        return {k: v for k, v in self.interfaces.items() if k in keys}


@dataclass
class Result:
    ok: bool
    interface: str = ""
    error: str = ""


class MCPEngine:
    """World-agnostic MCP routing engine."""

    def __init__(self):
        self._layers: dict[str, Layer] = {}

    def register_layer(self, name: str, layer: Layer) -> None:
        self._layers[name] = layer

    def route(self, layer: str, call: dict, *, ctx: dict = None) -> Result:
        """Route one MCP call. Returns Result."""
        iface_name = call.get("interface", "")
        params = dict(call.get("params", {}))
        lyr = self._layers.get(layer)
        if not lyr:
            return Result(ok=False, interface=iface_name, error=f"layer '{layer}' 未注册")
        iface = lyr.interfaces.get(iface_name)
        if not iface:
            return Result(ok=False, interface=iface_name, error=f"接口 '{iface_name}' 不存在")
        errors = iface.validate(params)
        if errors:
            return Result(ok=False, interface=iface_name, error="; ".join(errors))
        # Inject caller from engine context — primitives use it for auth
        if ctx and "agent" in ctx:
            params.setdefault("caller", ctx["agent"])
        try:
            if ctx and "agent" in ctx and "world" in ctx:
                iface.handler(ctx["agent"], params, ctx["world"])
            else:
                iface.handler(**params)
            return Result(ok=True, interface=iface_name)
        except Exception as e:
            return Result(ok=False, interface=iface_name, error=str(e))

    def route_all(self, layered: dict[str, list[dict]], **ctx) -> dict[str, list[Result]]:
        """Route all MCP calls across layers. Batch."""
        results = {}
        for layer_name, calls in layered.items():
            results[layer_name] = [
                self.route(layer_name, call, ctx=ctx) for call in calls
            ]
        return results

    def tool_list(self, layer: str, *, role_keys: set[str] = None) -> str:
        """Generate MCP tool list for LLM prompt. role_keys filters interfaces (e.g. npc-specific)."""
        lyr = self._layers.get(layer)
        if not lyr:
            return ""
        ifaces = lyr.subset(role_keys) if role_keys else lyr.interfaces
        lines = [f"### {lyr.name} — MCP Tools"]
        for name, iface in sorted(ifaces.items()):
            lines.append(iface.to_prompt_line())
        return "\n".join(lines)

    @property
    def layers(self) -> dict[str, Layer]:
        return self._layers
