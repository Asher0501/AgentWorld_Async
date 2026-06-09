"""Witcher World — 物理层 NPC 接口实现。
每个函数 = 6 原语的组合。引擎不感知这些函数的内容。
"""


def take_out(agent, params: dict, world):
    """拿出物品到空间 — delta(npc,-) + spawn + delta(zone,+)"""
    entity_alias = params.get("entity", "")
    qty = int(params.get("qty", 1))
    if not entity_alias:
        return
    # Resolve
    type_id = world.alias_registry.get(entity_alias)
    if not type_id:
        return
    type_node = world.entities.get(type_id)
    if not type_node:
        return
    # Construct visual
    visual_look = f"{agent.name}手中的{type_node.name}"
    graph = world.graph
    # Execute
    graph.delta(src=agent.id, tgt=type_id, qty=-qty)
    graph.spawn(pos=agent.pos, zone=agent.zone, type_ref=type_id,
                visual_look=visual_look, r=1)
    graph.delta(src=agent.zone, tgt=type_id, qty=+qty)


def eat(agent, params: dict, world):
    """消耗食物减少饥饿 — delta(food,-) + delta(hunger,-)"""
    entity_alias = params.get("entity", "")
    qty = int(params.get("qty", 1))
    if not entity_alias:
        return
    type_id = world.alias_registry.get(entity_alias)
    if not type_id:
        return
    graph = world.graph
    graph.delta(src=agent.id, tgt=type_id, qty=-qty)
    graph.delta(entity=agent, attr="hunger", value=-qty * 10)


def hand_over(agent, params: dict, world):
    """把物品放到目标位置 — delta(from,-) + spawn(at_target) + delta(zone,+)"""
    entity_alias = params.get("entity", "")
    to_alias = params.get("to", "")
    qty = int(params.get("qty", 1))
    if not entity_alias or not to_alias:
        return
    type_id = world.alias_registry.get(entity_alias)
    to_entity_id = world.alias_registry.get(to_alias)
    if not type_id or not to_entity_id:
        return
    to_entity = world.entities.get(to_entity_id)
    if not to_entity:
        return
    type_node = world.entities.get(type_id)
    if not type_node:
        return
    visual_look = f"{agent.name}放在{to_entity.name}的{type_node.name}"
    graph = world.graph
    graph.delta(src=agent.id, tgt=type_id, qty=-qty)
    graph.spawn(pos=to_entity.pos, zone=to_entity.zone, type_ref=type_id,
                visual_look=visual_look, r=1)
    graph.delta(src=to_entity.zone, tgt=type_id, qty=+qty)


def pick_up(agent, params: dict, world):
    """捡起空间中的物品 — delta(zone,-) + delta(npc,+) + despawn"""
    entity_alias = params.get("entity", "")
    qty = int(params.get("qty", 1))
    if not entity_alias:
        return
    entity_id = world.alias_registry.get(entity_alias)
    if not entity_id:
        return
    entity = world.entities.get(entity_id)
    if not entity:
        return
    type_ref = getattr(entity, "type_ref", "")
    if not type_ref:
        return
    graph = world.graph
    graph.delta(src=entity.zone, tgt=type_ref, qty=-qty)
    graph.delta(src=agent.id, tgt=type_ref, qty=+qty)
    # Check if pile entity still has remaining qty
    remaining = graph.edges.get((entity.zone, type_ref), 0)
    if remaining <= 0:
        graph.despawn(entity=entity)


def forge(agent, params: dict, world):
    """锻造武器 — delta(ore,-) + spawn(weapon) + delta(zone,+)"""
    entity_alias = params.get("entity", "矿石")
    qty = int(params.get("qty", 3))
    type_id = world.alias_registry.get(entity_alias)
    if not type_id:
        return
    type_node = world.entities.get(type_id)
    if not type_node:
        return
    weapon_id = world.alias_registry.get("武器")
    if not weapon_id:
        return
    visual_look = f"{agent.name}锻造的钢剑"
    graph = world.graph
    graph.delta(src=agent.id, tgt=type_id, qty=-qty)
    graph.spawn(pos=agent.pos, zone=agent.zone, type_ref=weapon_id,
                visual_look=visual_look, r=3)
    graph.delta(src=agent.zone, tgt=weapon_id, qty=+1)


def gather(agent, params: dict, world):
    """采集草药 — delta(zone,-) + delta(npc,+)"""
    entity_alias = params.get("entity", "草药")
    qty = int(params.get("qty", 3))
    type_id = world.alias_registry.get(entity_alias)
    if not type_id:
        return
    graph = world.graph
    graph.delta(src=agent.zone, tgt=type_id, qty=-qty)
    graph.delta(src=agent.id, tgt=type_id, qty=+qty)


def brew(agent, params: dict, world):
    """酿造麦酒 — delta(food,-) + delta(zone,+)"""
    entity_alias = params.get("entity", "食物")
    qty = int(params.get("qty", 2))
    type_id = world.alias_registry.get(entity_alias)
    if not type_id:
        return
    graph = world.graph
    graph.delta(src=agent.id, tgt=type_id, qty=-qty)
    graph.delta(src=agent.zone, tgt=type_id, qty=+qty)
