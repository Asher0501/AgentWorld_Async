"""AutoGenSim demo — run AgentWorld + AutoGenSim end-to-end.

Requires:
  1. AgentWorld running with dashboard:
     python main.py --dashboard 8766 --world AutoGenSim/office.yaml --runtime 300

  2. AutoGen installed:
     pip install autogen-agentchat autogen-ext[openai]

  3. Run this demo:
     python AutoGenSim/demo.py

Deleting this file leaves AgentWorld and AutoGenSim/office.yaml fully operational.
"""
import asyncio
from scheduler import AgentWorldTeam


async def main():
    team = AgentWorldTeam(director_url="http://localhost:8766")

    task = (
        "实现一个简单的 REST API：POST /todos 创建待办事项，GET /todos 获取列表。"
        "用 Python Flask 实现。"
        "小李写后端代码，小王写前端，老王审查。"
    )

    print("=" * 60)
    print("  AutoGenSim — Coding Task Demo")
    print("=" * 60)
    print(f"\n  Task: {task}\n")
    print("  AutoGen agents controlling AgentWorld NPCs via Director API...\n")

    result = await team.run(task)

    print(f"\n  Result:\n{result}")
    print(f"\n  Done. NPCs released back to autonomous mode.")


if __name__ == "__main__":
    asyncio.run(main())
