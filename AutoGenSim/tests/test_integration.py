#!/usr/bin/env python3
"""Integration test for Director API + AutoGen — requires AgentWorld core."""
import sys, os, asyncio

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, ROOT)  # dashboard/ is at project root, not under src/
sys.path.insert(0, os.path.join(ROOT, "AutoGenSim"))


async def test_director_client():
    from event_bus import EventBus
    from dashboard.server import start_dashboard
    from core.director import Director
    from core.world import World
    from systems.sensory import SensorySystem
    from systems.interaction import InteractionSystem
    from systems.decay import DecaySystem
    from llm.client import LLMClient
    import yaml

    with open(os.path.join(ROOT, "AutoGenSim", "office.yaml")) as f:
        wc = yaml.safe_load(f)
    with open(os.path.join(ROOT, "config", "llm.yaml")) as f:
        lc = yaml.safe_load(f)
    for p in lc["providers"].values():
        p["api_key"] = ""
    llm = LLMClient(lc["providers"]["deepseek"])
    world = World(wc, {"sensory": SensorySystem(), "interaction": InteractionSystem(llm, None), "decay": DecaySystem()})
    director = Director(world)

    d = asyncio.create_task(start_dashboard(EventBus(), director, 8765))
    await asyncio.sleep(0.5)

    from director_client import DirectorClient
    c = DirectorClient("http://localhost:8765")
    results = []

    s = await c.state()
    results.append(("GET /api/state", not s["frozen"], f"controlled={len(s['controlled'])}"))

    s = await c.snap("coder_01")
    results.append(("GET /api/snap", s["name"] == "小李", f"name={s['name']}, zone={s['zone']}"))

    await c.take("coder_01", level=2)
    await c.set("coder_01", "agent.main_thread", "Complete POST /todos")
    await c.memorize("coder_01", "REST API test passed")
    s = await c.snap("coder_01")
    ok = s["main_thread"] == "Complete POST /todos" and len(s["memory"]) == 1
    results.append(("take+set+memorize", ok, f"thread ok, mem={len(s['memory'])}, lvl={s['level']}"))

    await c.order("coder_01", {"action": "walk to break room"})
    results.append(("POST /api/order", True, "action sent"))

    await c.release("coder_01")
    s = await c.state()
    results.append(("POST /api/release", "coder_01" not in s["controlled"], f"free"))

    d.cancel()
    return results


def test_autogen_imports():
    results = []
    try:
        from autogen_agentchat.agents import AssistantAgent
        results.append(("AssistantAgent", True, "v0.7.5"))
    except Exception as e:
        results.append(("AssistantAgent", False, str(e)[:50]))
    try:
        from autogen_core.tools import FunctionTool
        results.append(("FunctionTool", True, "OK"))
    except Exception as e:
        results.append(("FunctionTool", False, str(e)[:50]))
    try:
        from director_client import DirectorClient
        from tools import make_tools
        tools = make_tools(DirectorClient())
        results.append(("make_tools", len(tools) == 3, f"{len(tools)} tools"))
    except Exception as e:
        results.append(("make_tools", False, str(e)[:50]))
    try:
        from autogen_core.tools import FunctionTool
        from tools import make_tools
        tools = make_tools(DirectorClient())
        [FunctionTool(t, description="x") for t in tools]
        results.append(("FunctionTool wrap", True, "3 wrapped"))
    except Exception as e:
        results.append(("FunctionTool wrap", False, str(e)[:50]))
    return results


def test_permissions():
    from core.director import Director
    from core.world import World
    from systems.sensory import SensorySystem
    from systems.interaction import InteractionSystem
    from systems.decay import DecaySystem
    from llm.client import LLMClient
    import yaml

    with open(os.path.join(ROOT, "AutoGenSim", "office.yaml")) as f:
        wc = yaml.safe_load(f)
    with open(os.path.join(ROOT, "config", "llm.yaml")) as f:
        lc = yaml.safe_load(f)
    for p in lc["providers"].values():
        p["api_key"] = ""
    llm = LLMClient(lc["providers"]["deepseek"])
    world = World(wc, {"sensory": SensorySystem(), "interaction": InteractionSystem(llm, None), "decay": DecaySystem()})
    director = Director(world)
    results = []

    director.take("coder_01", level=1)
    try:
        director.set("coder_01", "agent.pos", [50, 50])
        results.append(("level1 reject pos", False, "no error"))
    except PermissionError:
        results.append(("level1 reject pos", True, "PermissionError"))

    director.take("coder_01", level=2)
    director.set("coder_01", "agent.main_thread", "test")
    results.append(("level2 set thread", director.snap("coder_01")["main_thread"] == "test", "ok"))

    director.memorize("coder_01", "mem test")
    results.append(("level2 memorize", len(director.snap("coder_01")["memory"]) > 0, "ok"))

    return results


if __name__ == "__main__":
    print("=" * 60)
    print("  AgentWorld Async — Integration Test Report")
    print("=" * 60)

    suites = [
        ("DirectorClient API", asyncio.run(test_director_client())),
        ("AutoGen imports + tools", test_autogen_imports()),
        ("Permission levels", test_permissions()),
    ]

    total_ok = 0
    total = 0
    for name, results in suites:
        print(f"\n── {name} ──")
        for n, ok, detail in results:
            print(f"  {'✅' if ok else '❌'} {n:30s} | {detail}")
        ok_count = sum(1 for _, o, _ in results if o)
        total_ok += ok_count
        total += len(results)
        print(f"  → {ok_count}/{len(results)} passed")

    print(f"\n{'='*60}")
    print(f"  TOTAL: {total_ok}/{total} passed")
    print(f"  {'✅ ALL PASSED' if total_ok == total else '❌ SOME FAILED'}")
    print(f"{'='*60}")
