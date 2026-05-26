"""Tools that AutoGen agents can call — wraps DirectorClient methods."""
from .director_client import DirectorClient


def make_tools(director: DirectorClient):
    """Create tool functions bound to a DirectorClient instance."""

    async def order_npc(npc_id: str, action: str, dialogue: str = "") -> str:
        """Order an NPC to perform an action. npc_id like 'coder_01'.
        action is free text like '实现POST /todos端点'.
        """
        decision = {"action": action}
        if dialogue:
            decision["dialogue"] = dialogue
        await director.order(npc_id, decision)
        return f"已向 {npc_id} 发送指令: {action}"

    async def snap_npc(npc_id: str) -> str:
        """Get NPC's current state: zone, pos, drives, memory entries, main_thread."""
        snap = await director.snap(npc_id)
        lines = [
            f"{snap.get('name', npc_id)}: zone={snap.get('zone')} pos={snap.get('pos')}",
            f"drives={snap.get('drives', {})}",
            f"main_thread={snap.get('main_thread', '')}",
            f"memory ({len(snap.get('memory', []))} entries):",
        ]
        for m in snap.get("memory", [])[-5:]:
            lines.append(f"  - {m}")
        return "\n".join(lines)

    async def memorize_npc(npc_id: str, text: str) -> str:
        """Record a memory entry for an NPC — NPC will recall this in future decisions."""
        await director.memorize(npc_id, text)
        return f"已记录到 {npc_id} 的记忆: {text}"

    return [order_npc, snap_npc, memorize_npc]
