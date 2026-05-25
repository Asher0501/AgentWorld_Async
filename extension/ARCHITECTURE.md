# Extension Architecture — AgentWorld Async

<p align="center">
  <img src="img/ARCHITECTURE.png" alt="Architecture" width="100%">
</p>

## Overview

The `extension/` layer turns AgentWorld from an **autonomous simulation engine** into a **production multi-agent collaboration platform**. It adds three capabilities:

1. **Standard protocols** (MCP, A2A) — so external agents can discover, communicate with, and delegate tasks to AgentWorld NPCs
2. **Framework adapters** (AutoGen, CrewAI, LangGraph) — thin wrappers that map each framework's concepts to AgentWorld's primitives
3. **Function calling** — so AgentWorld NPCs can call external tools (APIs, databases) instead of only interacting with in-world entities

---

## Core Thesis

> **AgentWorld is not a competitor to AutoGen, CrewAI, or LangGraph. It is the physical layer they lack.**

| Framework provides... | AgentWorld provides... |
|----------------------|----------------------|
| Task delegation logic | Spatial execution (where + how long) |
| Role assignment | Sensory constraints (who is nearby to see/hear) |
| Workflow orchestration | Autonomous co-agents (NPCs acting independently) |
| Tool calling | World persistence + drive decay + spatial grid |

---

## Layer Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  COLLABORATION LAYER                                          │
│  AutoGen · CrewAI · LangGraph · OpenAI SDK                    │
│  Task delegation · Workflow · Role assignment · Tool calling  │
├──────────────────────────────────────────────────────────────┤
│  PROTOCOL LAYER (extension/protocols/)                        │
│  A2A: Agent Card · SendTask · GetTask                         │
│  MCP: world_perceive · world_act · world_spawn · world_snap   │
├──────────────────────────────────────────────────────────────┤
│  SIMULATION LAYER (src/)                                      │
│  SpatialGrid · SensorySystem · DeltaGate · Drives             │
│  14 YAML Slots · Per-Agent Traits · Intent Context            │
│  Gateway API · Director · Dashboard · SessionManager          │
└──────────────────────────────────────────────────────────────┘
```

**Each layer is independently deletable.** Remove `extension/` → AgentWorld still runs as a standalone simulation. Remove `src/` and keep `extension/` → lose the world engine, keep protocol skeletons.

---

## Protocol Layer Design

### MCP: Agent ↔ Tool (Anthropic Standard)

**Role:** An external host (CLI, IDE, another agent) calls AgentWorld as if it were a tool. The host doesn't care about AgentWorld's internals — it sees a flat tool list.

**Flow:**
```
External Host (MCP Client)
    │
    │  "list_tools()"
    ▼
MCP Server (extension/protocols/mcp/server.py)
    │
    │  Returns: [world_perceive, world_act, world_spawn, ...]
    ▼
External Host selects tool:
    │
    │  world_act(agent_id="geralt", decision={action: "walk to bar", duration: 5})
    ▼
MCP Server → AgentWorld Gateway → Director.order(geralt, decision)
    │
    │  AgentWorld Loop: Phase 4 ENQUEUE → Phase 0.5 FLUSH → execute
    ▼
Result: {status: "ok", narrative: "Geralt walked to the bar..."}
```

**Why MCP + AgentWorld is unique:**

- **Spatial constraints are real.** `world_act` with `{action: "walk to swamp"}` doesn't teleport — AgentWorld computes distance, duration, and gate traversal
- **Sensory feedback is grounded.** After execution, `world_perceive` returns only what the agent *actually* sees within `view_radius`
- **Autonomous NPCs coexist.** While one agent is under MCP control, others act independently via KL gate

### A2A: Agent ↔ Agent (Google Standard)

**Role:** An external agent discovers AgentWorld NPCs by name and delegates tasks to them. Unlike MCP (which treats AgentWorld as a monolithic tool), A2A treats each NPC as an independent agent with its own identity card.

**Flow:**
```
External Agent (AutoGen Executor)
    │
    │  "I need someone who can track monsters. Who's available?"
    ▼
GET /a2a/geralt/card
    │
    ▼
Agent Card Response:
{
  "name": "Geralt of Rivia",
  "capabilities": {
    "skills": ["combat", "tracking", "alchemy"],
    "location": {"zone": "bar_zone", "pos": [24, 17]},
    "drives": {"thirst": 60, "hunger": 50, "mood": 50}
  },
  "supportedTasks": ["investigate", "negotiate"],
  "url": "http://localhost:8766/a2a/geralt"
}
    │
    │  "Geralt is in the tavern. I'll send him to track the griffin."
    ▼
POST /a2a/geralt/tasks
{
  "task": "investigate_griffin",
  "params": {"location": "swamp_northeast", "method": "track_footprints"},
  "priority": "high"
}
    │
    ▼
A2A Handler → AgentWorld Director → AgentLoop → Sensory feedback → Result
```

**Agent Card auto-generation:** Each NPC's card is dynamically generated from its `AgentLayer` fields — no manual card creation. When an NPC moves zones, its card updates automatically. When an NPC's drives change (hunger, mood), the card reflects it.

---

## Framework Adapters

### AutoGen Integration

**Scenario:** A team of AutoGen agents (Planner, Executor, Analyst) collaboratively investigates a griffin sighting in White Orchard. The Planner decides "interview the innkeeper," the Executor sends the task to Geralt via A2A, and the Analyst processes Geralt's sensory findings.

**Key mapping:**
| AutoGen Concept | AgentWorld Equivalent |
|----------------|---------------------|
| `AssistantAgent` | External control via Director/A2A |
| `GroupChat` | AgentWorld's conversation_buffer + sensory channels |
| `ToolAgent` | MCP `world_perceive` / `world_act` |
| `task.result()` | A2A `GetTask` after NPC finishes action |

**Demo file:** `extension/frameworks/autogen/witcher_investigation.py`

### CrewAI Integration

**Scenario:** CrewAI manages a Central Perk coffee shop. The Manager (Gunther) assigns the Barista (Rachel) and Janitor (Chandler) roles. CrewAI orchestrates the workflow, while AgentWorld simulates the physical coffee shop—Joey walks in hungry, Ross orders coffee, Phoebe plays guitar. CrewAI's managed agents coexist with AgentWorld's autonomous NPCs.

**Key mapping:**
| CrewAI Concept | AgentWorld Equivalent |
|---------------|---------------------|
| `Agent` with role | NPC controlled via Director |
| `Task` | Orchestrated action injected via A2A |
| `Crew` | A2A task queue + Agent Cards |
| Autonomous NPCs | AgentWorld's KL gate-driven NPCs (not managed by CrewAI) |

**Demo file:** `extension/frameworks/crewai/coffee_shop.py`

### LangGraph Integration (Paper-Quality)

**Scenario:** AgentWorld's slot architecture (14 slots organized in 3 layers, with conditional rendering and ordered priority) maps directly onto LangGraph's StateGraph primitives. This validates the universality of the Slot Vector Architecture — it is not a quirk of one engine, but a generalizable pattern for declarative cognition in any state-machine framework.

**Key mapping:**
| LangGraph Concept | AgentWorld SVA Equivalent |
|------------------|--------------------------|
| `StateGraph` | `prompts.yaml` template + slot list |
| `Node` | Individual slot (renders a `safe_format` template) |
| `ConditionalEdge` | Slot `condition:` field (activates only if `ctx[key]` is truthy) |
| `MessageGraph` | Slot order (determines attention priority) |
| `Checkpoint` | AgentWorld `snapshot_p()` (P-distribution snapshot) |

**Demo file:** `extension/frameworks/langgraph/slot_mapping.py`

---

## Function Calling Schema

### Design

AgentWorld NPCs currently interact via natural-language `action` descriptions matched to nearby entities. For production use, agents must also be able to call structured external tools (APIs, databases).

**New output schema field:**

```json
{
  "function_call": {
    "name": "query_weather",
    "params": {"city": "Novigrad", "days": 3}
  }
}
```

**Flow:**

```
Agent decides → function_call in output
    │
    ▼
Agent Loop Phase 4 detects function_call
    │
    ▼
→ route to MCP tool handler (if matching tool exists)
→ execute tool
→ inject result into agent's prompt as a new slot: function_result
    │
    ▼
Next cycle: agent sees tool result in prompt → decides next action
```

**Slot addition:** A new `function_result` slot renders only when a tool was called in the previous cycle. The agent sees the tool's output as raw text — no engine interpretation.

---

## Use Cases

### 1. Witcher Investigation (AutoGen + A2A)
Full walkthrough in `extension/use_cases/witcher_investigation.md`

### 2. Coffee Shop Management (CrewAI + MCP)
Full walkthrough in `extension/use_cases/coffee_shop_management.md`

### 3. Spider-Man Patrol (AgentWorld Autonomous)
Full walkthrough in `extension/use_cases/spiderman_patrol.md`

### 4. Cross-World Agent Migration
Full walkthrough in `extension/use_cases/cross_world_agent.md`

---

## Implementation Status

| Component | Status | Priority |
|-----------|--------|----------|
| `extension/README.md` | ✅ Complete | — |
| `extension/ARCHITECTURE.md` | ✅ Complete | — |
| `extension/img/` (3 diagrams) | ✅ Complete | — |
| `extension/protocols/mcp/server.py` | 📋 Designed | P0 |
| `extension/protocols/mcp/README.md` | 📋 Designed | P0 |
| `extension/protocols/a2a/` | 📋 Designed | P0 |
| `extension/frameworks/autogen/` | 📋 Designed | P1 |
| `extension/frameworks/crewai/` | 📋 Designed | P1 |
| `extension/frameworks/langgraph/` | 📋 Designed | P2 |
| `extension/function_calling/` | 📋 Designed | P1 |
| `extension/use_cases/` | 📋 Designed | P2 |

**Next step:** Implement MCP server (smallest scope, highest immediate value).
