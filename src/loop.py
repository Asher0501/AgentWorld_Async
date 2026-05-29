"""Agent loop — phase-based pipeline. All config injected via LoopConfig.

Phase order: sense → KL gate → decide → act
Each phase may skip the remainder via continue.
"""
import time
import asyncio
from dataclasses import dataclass, field
from core.delta_gate import total_delta, snapshot_p


@dataclass
class LoopConfig:
    """Structured config for agent loop — type-safe, self-documenting."""
    poll_interval: float = 0.3
    thresholds: list = field(default_factory=lambda: [30, 60, 80])
    coin_epsilon: float = 5
    stale_timeout: float = 30
    currency: str = "coins"
    text: dict = field(default_factory=dict)
    labels: dict = field(default_factory=dict)
    default_patience: int = 5
    memory_prompt_count: int = 5
    file_output_dir: str = "AutoGenSim/output"


def _build_decision_ctx(agent, al, world, sensory, assembler, cfg, delta_text) -> dict:
    """Collect all ctx fields from channel sources. No formatting, no judgment."""
    ctx = {}
    channel = assembler.channel
    channel.collect(ctx,
                    agent=agent, al=al, world=world,
                    sensory=sensory, cfg=cfg,
                    delta_text=delta_text, loader=assembler.loader)
    return ctx


# ── main loop ──

async def run_agent(agent, world, brain, assembler, systems,
                    runtime: float, *, cfg: LoopConfig = None,
                    director=None, dashboard_emit=None):
    if cfg is None:
        cfg = LoopConfig()
    name = agent.name
    al = agent.get("agent")
    end = time.time() + runtime
    interaction = systems["interaction"]
    labels = cfg.labels

    from logger import log
    err_backoff: dict[str, int] = {}
    while time.time() < end:
        try:
            # ═══════════════════════════════════════════
            #  FREEZE CHECK
            # ═══════════════════════════════════════════
            if director and director.frozen:
                await asyncio.sleep(cfg.poll_interval)
                continue

            # ═══════════════════════════════════════════
            #  PHASE 0.5: FLUSH — execute enqueued action when its duration expires
            # ═══════════════════════════════════════════
            drives = al.drives
            coins = round(float(agent.get("interaction").private_attrs.get(cfg.currency, 0)))
            if al._pending_action is not None and time.time() >= al._action_complete_at:
                enqueued_decision, enqueued_target = al._pending_action
                # Execute the delayed action now — write layers, apply deltas
                target_name = enqueued_decision.get("target_name")
                action_text = enqueued_decision.get("action")
                if target_name and action_text:
                    target = interaction.find_entity_by_name(
                        agent.zone, target_name, world.entities, exclude_id=agent.id)
                    if target and interaction.can_interact(agent, target):
                        result = await interaction.interact(agent, target, enqueued_decision, world)
                        agent.last_action_time = world.clock.now()
                        al._last_target_name = target.name
                        al._last_expects_reply = bool(enqueued_decision.get("expects_reply"))
                        al._last_intent = enqueued_decision.get("intent", "")
                        al._last_action_ts = time.time()
                        al._last_action_drives = {k: round(float(v), 1) for k, v in drives.attrs.items()}
                        log.result(name, action=action_text,
                                   target=target_name, target_id=target.id,
                                   narrative=result.narrative,
                                   deltas=result.caller_deltas,
                                   drives={k: round(float(v), 1) for k, v in drives.attrs.items()},
                                   sim=world.clock.now(),
                                   thread_done=enqueued_decision.get("thread_completed", False),
                                   duration=enqueued_decision.get("duration", 3.0),
                                   file_output=enqueued_decision.get("file_output"))
                        if dashboard_emit:
                            dashboard_emit({"agent": name, "zone": agent.zone,
                                            "phase": "action",
                                            "action_text": action_text,
                                            "dialogue": enqueued_decision.get("dialogue", ""),
                                            "story": enqueued_decision.get("story", ""),
                                            "target_name": target_name,
                                            "drives": {k: round(float(v), 1) for k, v in drives.attrs.items()},
                                            "coins": coins,
                                            "intent": enqueued_decision.get("intent", ""),
                                            "main_thread": enqueued_decision.get("main_thread", ""),
                                            "thread_completed": enqueued_decision.get("thread_completed", False)})
                    elif target and not interaction.can_interact(agent, target):
                        agent.move_to(list(target.pos))
                        agent.last_action_time = world.clock.now()
                        systems["sensory"].update(agent, world.entities, world,
                                                   channel_configs=labels.get("sensory_prompts"))
                snapshot_p(al, sensory, drives, cfg.currency, cfg.text,
                           cfg.thresholds, cfg.coin_epsilon)
                # NPC file output: write to disk as part of action execution
                fo = enqueued_decision.get("file_output", {})
                if fo and fo.get("filename") and fo.get("content"):
                    import os as _os
                    out_dir = os.path.join(os.path.dirname(
                        os.path.dirname(os.path.abspath(__file__))), cfg.file_output_dir)
                    _os.makedirs(out_dir, exist_ok=True)
                    out_path = _os.path.join(out_dir, f"{agent.id}_{fo['filename']}")
                    with open(out_path, "w") as _f:
                        _f.write(fo["content"])
                al._pending_action = None  # cleared only after successful execution
                await asyncio.sleep(0)
                continue

            # ═══════════════════════════════════════════
            #  PHASE 1: SENSE
            # ═══════════════════════════════════════════
            elapsed = max(world.clock.now() - agent.last_action_time, 0)
            systems["decay"].tick(agent, elapsed)
            systems["sensory"].update(agent, world.entities, world,
                                       channel_configs=labels.get("sensory_prompts"))
            sensory = al.sensory
            zone_entities = [e for e in world.entities.values() if e.zone == agent.zone]
            if dashboard_emit:
                vis = sensory.channels.get("visual", {})
                aud = sensory.channels.get("auditory", {})
                zone_def = world.zones.get(agent.zone, {})
                entity_list = []
                for e in zone_entities:
                    etype = "agent" if e.has("agent") else "gate" if e.get("interaction") and e.get("interaction").gate else "item"
                    entity_list.append({"id": e.id, "name": e.name, "type": etype, "pos": list(e.pos)})
                dashboard_emit({"agent": name, "zone": agent.zone,
                                "zone_width": zone_def.get("width", 40),
                                "zone_height": zone_def.get("height", 30),
                                "phase": "sensory",
                                "entities": entity_list,
                                "visual": [{"name": r.name, "distance": r.distance, "look": r.data.get("look", "")}
                                           for r in vis.values()],
                                "auditory": [{"name": r.name, "speech": r.data.get("current_speech", "")}
                                            for r in aud.values()]})

            # Controlled agent: execute external order or skip Phase 2/3 entirely
            if director and director.is_controlled(agent.id):
                decision = director.pending(agent.id)
                if decision:
                    # Skip directly to Phase 4 — no KL gate, no LLM call
                    target_name = decision.get("target_name")
                    action_text = decision.get("action")
                    if action_text:
                        target = interaction.find_entity_by_name(
                            agent.zone, target_name, world.entities,
                            exclude_id=agent.id) if target_name else None
                        if target and interaction.can_interact(agent, target):
                            al._pending_action = (decision, target)
                            al._action_complete_at = time.time() + max(0.5, decision.get("duration", 3.0))
                        elif target and not interaction.can_interact(agent, target):
                            agent.move_to(list(target.pos))
                            agent.last_action_time = world.clock.now()
                        else:
                            al._pending_action = (decision, None)
                            al._action_complete_at = time.time()
                    snapshot_p(al, sensory, drives, cfg.currency, cfg.text,
                               cfg.thresholds, cfg.coin_epsilon)
                    await asyncio.sleep(0)
                else:
                    await asyncio.sleep(cfg.poll_interval)
                continue

            # ═══════════════════════════════════════════
            #  PHASE 2: GATE
            # ═══════════════════════════════════════════
            delta_text = total_delta(al, sensory, drives, cfg.currency, cfg.text,
                                 cfg.thresholds, cfg.coin_epsilon, cfg.stale_timeout)

            if not delta_text:
                await asyncio.sleep(cfg.poll_interval)
                continue

            log.gate(name, triggered=True,
                     reason=delta_text, zone=agent.zone,
                     nearby=len(zone_entities),
                     drives={k: round(float(v), 1) for k, v in drives.attrs.items()},
                     pos=agent.pos, coins=coins)

            # ═══════════════════════════════════════════
            #  PHASE 3: DECIDE
            # ═══════════════════════════════════════════
            # Action pacing: skip if still executing prior action
            if time.time() < al._action_complete_at:
                await asyncio.sleep(cfg.poll_interval)
                continue

            # Write-pending lock: skip one cycle after interacting
            # Ensures sensory consistency — agent's own action absorbed before next decision
            if al._write_pending:
                al._write_pending = False
                snapshot_p(al, sensory, drives, cfg.currency, cfg.text,
                           cfg.thresholds, cfg.coin_epsilon)
                await asyncio.sleep(cfg.poll_interval)
                continue

            ctx = _build_decision_ctx(agent, al, world, sensory, assembler, cfg, delta_text)

            decision = await brain.decide(ctx, template_name=al.template or "agent_decision",
                                           provider=al.llm_provider, slot_mask=al.slot_mask)
            if dashboard_emit:
                dashboard_emit({"agent": name, "zone": agent.zone,
                                "phase": "decision",
                                "intent": decision.get("intent", ""),
                                "thinking": decision.get("thinking", ""),
                                "main_thread": decision.get("main_thread", ""),
                                "internal": decision.get("internal", "")})
            if decision.get("main_thread"):
                al.main_thread = decision["main_thread"]

            # ═══════════════════════════════════════════
            #  PHASE 4: ENQUEUE — store action for delayed execution
            # ═══════════════════════════════════════════
            target_name = decision.get("target_name")
            action_text = decision.get("action")
            if action_text:
                target = interaction.find_entity_by_name(
                    agent.zone, target_name, world.entities,
                    exclude_id=agent.id) if target_name else None
                log.decide(name, action=action_text,
                           intent=decision.get("intent", ""),
                           target=target_name,
                           target_id=target.id if target else "",
                           llm_output=decision,
                           tokens=getattr(brain, '_last_tokens', 0),
                           latency=getattr(brain, '_last_latency', 0.0))
                if target and interaction.can_interact(agent, target):
                    al._pending_action = (decision, target)
                    al._action_complete_at = time.time() + max(0.5, decision.get("duration", 3.0))
                elif target and not interaction.can_interact(agent, target):
                    agent.move_to(list(target.pos))
                    agent.last_action_time = world.clock.now()
                    systems["sensory"].update(agent, world.entities, world,
                                               channel_configs=labels.get("sensory_prompts"))
                else:
                    # No target or can't find — direct enqueue (for controlled NPC with file_output etc.)
                    al._pending_action = (decision, None)
                    al._action_complete_at = time.time()
            snapshot_p(al, sensory, drives, cfg.currency, cfg.text,
                       cfg.thresholds, cfg.coin_epsilon)
            await asyncio.sleep(0)

        except Exception as e:
            log.error(agent=name, module=f"loop.{name}", exception=e)
            # Transient (rate-limit, timeout) → backoff. Fatal → short pause.
            etype = type(e).__name__
            transient = etype in ("RateLimitError", "APITimeoutError", "Timeout", "TimeoutError")
            err_backoff[name] = err_backoff.get(name, 0) + 1 if transient else 0
            delay = min(2 ** err_backoff.get(name, 1), 60) if transient else 3
            await asyncio.sleep(delay)
