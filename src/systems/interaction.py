"""InteractionSystem — engine single entry point.
interact(): routes LLM calls to physical (agent.interfaces) or abstract (graph.primitives).
Zero op-name branching. Zero domain vocabulary.
"""
import json
import time
from dataclasses import dataclass, field


@dataclass
class ActionResult:
    target_id: str = ""
    caller_deltas: dict = field(default_factory=dict)
    narrative: str = ""
    llm2_prompt: str = ""
    llm2_output: str = ""


class InteractionSystem:
    def __init__(self, llm=None, assembler=None):
        self.llm = llm
        self.assembler = assembler

    # ═══════════ public API ═══════════

    def can_interact(self, agent, target) -> bool:
        if not target.has("interaction"):
            return False
        agent_layer = agent.get("agent")
        agent_r = agent_layer.interaction_radius if agent_layer else 0
        target_r = target.get("interaction").interaction_radius
        return agent.distance_to(target) <= min(agent_r, target_r)

    def find_entity_by_name(self, zone: str, name: str,
                             all_entities: dict, exclude_id: str = "") -> object | None:
        match = None
        for e in all_entities.values():
            if e.zone != zone or not e.has("interaction"):
                continue
            if e.id == exclude_id:
                continue
            if e.name == name:
                if match is not None:
                    return None
                match = e
        return match

    # ═══════════ core: interact() ═══════════

    async def interact(self, agent, target,
                       decision: dict, world) -> ActionResult | None:
        """Engine single entry point. Two-slot dispatch:
        physical_calls → agent.interfaces[name](params)
        abstract_calls → graph.primitives[name](params)
        """
        target_inter = target.get("interaction")
        agent_layer = agent.get("agent")
        dialogue = decision.get("dialogue", "")
        story = decision.get("story", "")

        # ── MCP Engine dispatch ──
        if hasattr(world, "mcp"):
            world.mcp.route_all({
                "physical": decision.get("physical_calls") or [],
                "abstract": decision.get("abstract_calls") or [],
            }, agent=agent, world=world)

        # ── Layer write (config-driven via layer_registry writable) ──
        self._write_agent_layers(agent, agent_layer, decision,
                                 dialogue, story, world)

        if agent_layer:
            agent_layer._write_pending = True

        # NPC→NPC: done
        if target.has("agent"):
            return ActionResult(
                target_id=target.id,
                narrative=story or dialogue or "",
            )

        # NPC→Item: interact_narrative LLM
        narrative = story or ""
        action_text = decision.get("action", "")
        narrative, llm2_prompt, llm2_output = await self._resolve_npc_item(
            agent, target, action_text, story, narrative, world)

        self._handle_gate_transfer(agent, target_inter, world)

        return ActionResult(
            target_id=target.id,
            narrative=narrative,
            llm2_prompt=llm2_prompt,
            llm2_output=llm2_output,
        )

    def _write_agent_layers(self, agent, agent_layer, decision, dialogue, visual, world=None):
        """Generic layer write: iterate layer_registry.writable, mapping LLM fields -> layer properties."""
        layer_registry = getattr(world, "_layer_registry", {}) if world else {}
        for layer_name, reg in layer_registry.items():
            if not agent.has(layer_name):
                continue
            writable = reg.get("writable", {})
            layer = agent.get(layer_name)
            for field, prop in writable.items():
                value = decision.get(field)
                if value:
                    layer.properties[prop] = value
                    if field == "dialogue":
                        layer.properties.setdefault("speech_ts", time.time())

        if dialogue and agent_layer:
            agent_layer._conversation_buffer.append(
                {"speaker": agent.name, "text": dialogue, "ts": time.time()})
            if len(agent_layer._conversation_buffer) > 8:
                agent_layer._conversation_buffer.pop(0)
        if agent_layer and decision.get("remember"):
            mem = decision.get("story", "") or decision.get("action", "")
            if mem:
                agent_layer.memory.record(mem)

    async def _resolve_npc_item(self, agent, target, action_text, story, fallback_narrative, world=None):
        narrative = fallback_narrative
        llm2_prompt, llm2_output = "", ""
        target_inter = target.get("interaction")
        if not self.llm or not self.assembler:
            return narrative, llm2_prompt, llm2_output
        try:
            agent_inter = agent.get("interaction").private_attrs if agent.has("interaction") else {}
            context = {
                "action_description": action_text or story or "",
                "caller_name": agent.name,
                "caller_personality": agent.get("agent").personality if agent.has("agent") else "",
                "caller_state": json.dumps(agent_inter, ensure_ascii=False),
                "caller_id": agent.id,
                "target_name": target.name,
                "target_description": target_inter.properties.get("description", "") if target_inter.properties else getattr(target, 'describe', '') or target.name,
                "target_hidden": json.dumps(target_inter.hidden, ensure_ascii=False) if target_inter.hidden else "",
                "target_context": "",
                "target_id": target.id,
            }
            llm2_prompt = self.assembler.assemble("interact_narrative", context)
            system = self.assembler.get_system_prompt("interact_narrative")
            schema = self.assembler.get_output_schema("interact_narrative")
            temp = self.assembler.get_temperature("interact_narrative")
            raw = await self.llm.chat(system=system, messages=[{"role": "user", "content": llm2_prompt}],
                                       temperature=temp, response_format=schema)
            llm2_output = raw
            from agent.brain import _parse_llm_json
            data = _parse_llm_json(raw, "interact_narrative")
            narrative = data.get("narrative", narrative)
            deltas = data.get("deltas", {})
            extra = deltas.get(agent.id, {})
            if extra:
                self._apply_deltas(agent, extra)
            target_changes = data.get("target_changes", {})
            if target_changes and target_inter and not target_inter.readonly:
                world.update_entity(target.id, target_changes)
        except Exception as e:
            from logger import log
            log.error(agent=agent.name if agent else "unknown",
                      module="interaction._resolve_npc_item",
                      exception=e)
        if agent.has("agent") and narrative:
            agent.get("agent")._pending_narrative = narrative
        return narrative, llm2_prompt, llm2_output

    def _handle_gate_transfer(self, agent, target_inter, world):
        gate = target_inter.gate if target_inter else None
        if gate and hasattr(world, 'lifecycle'):
            world.lifecycle.transfer_zone(agent, gate["to_zone"],
                                           list(gate.get("to_pos", agent.pos)))

    def _apply_deltas(self, entity, deltas: dict) -> None:
        if not entity.has("interaction"):
            return
        entity.get("interaction").apply_deltas(deltas)
        from core.verification import verify
        inter = entity.get("interaction")
        issues = verify(entity, deltas, inter.currency_key,
                        inter.drive_min, inter.drive_max)
        if issues:
            from logger import log
            log.warning(agent=entity.id, module="verification",
                        message=f"{'; '.join(issues)}")
