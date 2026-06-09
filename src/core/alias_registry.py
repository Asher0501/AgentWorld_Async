"""Alias Registry — global alias → entity_id O(1) lookup.

Built from two sources:
  1. Spatial layer: entity.visual_look / entity.name
  2. Abstract layer: item_registry.yaml aliases → type_node

Sync: entities created/destroyed → alias_registry add/remove.
"""


def build_alias_registry(world, graph_engine, item_registry_cfg: dict) -> dict[str, str]:
    """Build global alias→entity_id dict from spatial + abstract layers."""
    reg = {}

    # Spatial layer first (lower priority), then abstract overrides
    for e in world.entities.values():
        if e.has("visual"):
            look = e.get("visual").properties.get("look", "")
            if look and look not in reg:
                reg[look] = e.id
        if e.name and e.name not in reg:
            reg[e.name] = e.id

    # Abstract layer overrides (higher priority)
    for alias in item_registry_cfg:
        type_node_id = f"type_{alias}"
        type_node = world.entities.get(type_node_id)
        if type_node:
            reg[alias] = type_node_id

    return reg
