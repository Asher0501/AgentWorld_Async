# AutoGenSim

**AutoGen agents controlling AgentWorld NPCs through Director API.**

This module demonstrates how AutoGen's multi-agent orchestration can drive AgentWorld's spatial NPCs — without modifying either codebase.

## Architecture

```
AutoGen GroupChat (reasoning)     →    Director API    →    AgentWorld NPCs (execution)
════════════════════════════      ═══  ═══════════════      ═══════════════════════
Planner agent (LLM)              →    order("coder_01",    →  小李 NPC executes action
  "write POST /todos"                  {action: ...})         (walks to desk, writes code)

Coder agent (LLM)                →    snap("coder_01")     →  returns NPC state
  "code written, tests pass"          memorize(...)         →  records in NPC memory
```

## Quick Start

```bash
# 1. Start AgentWorld (dashboard required for Director API)
python main.py --dashboard 8766 --world AutoGenSim/office.yaml --runtime 300

# 2. In another terminal, run the demo
pip install autogen-agentchat autogen-ext[openai]
python AutoGenSim/demo.py
```

## Deletion Test

| Delete | Impact |
|--------|--------|
| `AutoGenSim/` entire folder | AgentWorld runs normally with office.yaml as standalone simulation |
| `autogen-agentchat` (pip uninstall) | AgentWorld runs normally — AutoGen was never imported by src/ |
| AgentWorld (deleted) | AutoGenSim has no NPCs to control — scheduler fails gracefully |

## Files

- `office.yaml` — Office world config (6 NPCs, 3 zones, open space + meeting room + break room)
- `scheduler.py` — Main orchestration: creates AutoGen agents, runs tasks
- `director_client.py` — HTTP client for Director API
- `tools.py` — Tool definitions (order_npc, snap_npc, memorize_npc)
- `personas.py` — System prompts for each agent role
- `demo.py` — Runnable coding task demo
