"""AutoGenSim scheduler — AutoGen agents control AgentWorld NPCs via Director API.

Uses real AutoGen (autogen-agentchat) for agent orchestration.
Deleting this file (and AutoGenSim/) leaves AgentWorld fully operational.
"""
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.tools import FunctionTool

from director_client import DirectorClient
from personas import PLANNER_SYSTEM, CODER_SYSTEM, REVIEWER_SYSTEM


def make_tools(director: DirectorClient):
    """Create Director-tool functions bound to a DirectorClient instance."""

    async def order_npc(npc_id: str, action: str, dialogue: str = "") -> str:
        decision = {"action": action}
        if dialogue:
            decision["dialogue"] = dialogue
        await director.order(npc_id, decision)
        return f"Ordered {npc_id}: {action}"

    async def snap_npc(npc_id: str) -> str:
        s = await director.snap(npc_id)
        return (
            f"{s.get('name', npc_id)}: zone={s.get('zone')} pos={s.get('pos')}\n"
            f"drives={s.get('drives', {})}\n"
            f"main_thread={s.get('main_thread', '')}\n"
            f"memory: {s.get('memory', [])}"
        )

    async def memorize_npc(npc_id: str, text: str) -> str:
        await director.memorize(npc_id, text)
        return f"Memorized to {npc_id}: {text}"

    return [order_npc, snap_npc, memorize_npc]


class AgentWorldTeam:
    """Wraps AutoGen's RoundRobinGroupChat with AgentWorld NPC control."""

    def __init__(self, director_url: str = "http://localhost:8766", model: str = "gpt-4o"):
        self.director = DirectorClient(director_url)
        self.model = model

    async def _make_agent(self, name: str, system_prompt: str, npc_id: str) -> AssistantAgent:
        """Create an AutoGen AssistantAgent with Director tools."""
        tools = await self._make_tools()
        return AssistantAgent(
            name=name,
            model_client=OpenAIChatCompletionClient(model=self.model),
            tools=[
                FunctionTool(tools[0], description="Order an NPC to perform an action"),
                FunctionTool(tools[1], description="Check an NPC's current state"),
                FunctionTool(tools[2], description="Record a memory for an NPC"),
            ],
            system_message=system_prompt,
            reflect_on_tool_use=True,
        )

    async def _make_tools(self):
        return make_tools(self.director)

    async def run(self, task: str) -> str:
        """Run a coding task through the AutoGen team."""
        # Create agents
        planner = await self._make_agent("Planner", PLANNER_SYSTEM, "pm_01")
        coder = await self._make_agent("Coder", CODER_SYSTEM, "coder_01")
        reviewer = await self._make_agent("Reviewer", REVIEWER_SYSTEM, "reviewer_01")

        # RoundRobin team
        team = RoundRobinGroupChat(participants=[planner, coder, reviewer])

        # Take control of NPCs at moderator level
        for npc_id in ["pm_01", "coder_01", "coder_02", "reviewer_01", "designer_01", "intern_01"]:
            await self.director.take(npc_id, level=2)

        # Run task
        result = await team.run(task=task)

        # Release all NPCs — they return to autonomous mode
        for npc_id in ["pm_01", "coder_01", "coder_02", "reviewer_01", "designer_01", "intern_01"]:
            await self.director.release(npc_id)

        return str(result)


async def demo():
    """Run a simple demo — requires AgentWorld running on localhost:8766."""
    team = AgentWorldTeam(director_url="http://localhost:8766")
    result = await team.run(
        "实现一个简单的 REST API：POST /todos 创建待办事项，"
        "GET /todos 获取列表。用 Python Flask 实现。"
        "小李写后端，小王写前端，老王审查代码。"
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(demo())
