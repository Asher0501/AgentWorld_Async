<p align="center">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue?style=flat-square">
  <img src="https://img.shields.io/badge/tests-177-brightgreen?style=flat-square">
  <img src="https://img.shields.io/badge/engine%20primitives-6-orange?style=flat-square">
  <img src="https://img.shields.io/badge/license-MIT-brightgreen?style=flat-square">
</p>

<h1 align="center">AgentWorld Async</h1>

<p align="center">
  <b>Spatial Layer + Abstract Layer · 6 Primitives · MCP Interfaces<br/>
  Engine reports facts. LLM provides cognition.<br/>
  <sub>空间层 + 抽象层 · 6 原语 · MCP 接口 · 引擎报事实，LLM 做认知</sub></b>
</p>

---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LLM Layer (Cognition · 认知)                       │
│                                                                             │
│   Sensory sections per channel:                                             │
│   ┌─ Visual ──────────┐ ┌─ Inventory ───────┐ ┌─ Interactable ───────────┐ │
│   │ 杰洛特手中的金币     │ │ 金币 ×150         │ │ 杰洛特 — 聊两句           │ │
│   └───────────────────┘ └──────────────────┘ └───────────────────────────┘ │
│                                                                             │
│   MCP Tool List → LLM Decision:                                             │
│   { physical_calls: [{interface:"take_out", params:{entity:"金币",qty:5}}], │
│     abstract_calls: [{interface:"delta", params:{entity:"杰洛特",           │
│                        attr:"thirst", value:-10}}] }                        │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ two-slot dispatch
┌───────────────────────────────▼─────────────────────────────────────────────┐
│                         Engine Layer (Execution · 执行)                      │
│                                                                             │
│   interact(entity, interface, params) — single write entry                  │
│     physical_calls  → agent.interfaces[name]   (world-bound)                │
│     abstract_calls  → graph.primitives[name]   (engine built-in)            │
│                                                                             │
│   Channel Collector → auto-registered source classes                        │
│   Alias Registry    → O(1) dict: LLM string → entity_id                     │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
┌─────────▼──────────┐ ┌────────▼──────────┐ ┌────────▼──────────────────────┐
│  Spatial Layer     │ │  Abstract Layer   │ │  Interface Layer              │
│  (memory)          │ │  (edges dict/SQL) │ │  (world-bound YAML)           │
│                    │ │                   │ │                               │
│  entities + pos    │ │  type_node × N    │ │  npc_interfaces.yaml:          │
│  visual/auditory   │ │  edges:           │ │    take_out: delta+spawn       │
│  SpatialGrid       │ │    npc→type  qty  │ │    hand_over: delta+spawn      │
│                    │ │    zone→type  qty  │ │    eat: delta(edge)+delta(attr)│
│  spawn/despawn     │ │    npc→zone   qty  │ │    pick_up: delta+despawn      │
│  relocate          │ │                   │ │                               │
│                    │ │  delta/add_node    │ │  npc_actions.py: impl          │
│                    │ │  remove_node       │ │                               │
└────────────────────┘ └───────────────────┘ └───────────────────────────────┘
```

---

# 中文版

## 核心思想

### 1. 双层模型

| | 空间层 | 抽象层 |
|---|---|---|
| 职责 | "在哪里""长什么样" | "谁持有多少" |
| 存储 | 内存 (entities + SpatialGrid) | 内存 edges + SQLite |
| 边 | 无 — 物理相邻 | (src, tgt, qty) — 无类型 |
| 感官 | 视觉 / 听觉 / 可交互 | 持有（npc 的一阶邻居子图） |

NPC 和物品是同一个 `Entity` class。`type_ref` 字段把空间 entity 指向抽象层的 `type_node`。

**为什么分两层**：位置是物理事实，持有是逻辑事实。两者正交 — 各自管理独立维度。

### 2. MCP 接口模型

每个 NPC 在 YAML 中注册自己支持的接口。LLM 在 prompt 里看到 tool list，直接输出 tool call。

```
物理层 (physical_calls):
  take_out({entity, qty})      从持有中拿出物品到空间
  hand_over({entity, to, qty}) 把物品放到目标位置
  eat({entity, qty})           消耗食物
  pick_up({entity, qty})       捡起空间中的物品

抽象层 (abstract_calls):
  delta({src, tgt, qty})       边数值转移
  delta({entity, attr, value}) 属性变更
  spawn/despawn/relocate/add_node/remove_node
```

**引擎只有 `interact()` 一个入口** — 路由按字典查：`agent.interfaces[name]` 或 `graph.primitives[name]`。

### 3. 6 个引擎原语

| 原语 | 层 | 做什么 |
|---|---|---|
| `delta` | 通用 | 边 qty ± / 属性 ± |
| `spawn` | 空间 | entity 诞生 + visual + alias 注册 + 复用检查 |
| `despawn` | 空间 | entity 消失 + alias 注销 |
| `relocate` | 空间 | entity 改变位置 |
| `add_node` | 抽象 | 节点加入边系统 |
| `remove_node` | 抽象 | 节点脱离 + 清理关联边 |

引擎代码只有这 6 个词。`take_out`、`eat`、`forge` 在 YAML 和 LLM 的 vocab 里，不在引擎代码里。

### 4. 通道驱动感官

```
channel.py:
  _SOURCE_REGISTRY = [AgentLayerSource, WorldSource, DriveSource,
                       SensorySource, MemorySource, TraitsSource,
                       DeltaGateSource, GraphSource]

channels.yaml:
  - source: graph
    fields: [inventory_lines]     ← 持有层, 遍历 npc→type_node 边
```

**新增通道 = YAML + class。ChannelCollector 自动发现。loop.py 不改一行。**

### 5. 世界即配置

```
config/worlds/witcher/
  npc_interfaces.yaml    — 物理接口：take_out, hand_over, eat, forge...
  npc_actions.py         — 接口实现：delta + spawn 组合

src/worlds/magic/
  npc_interfaces.yaml    — 换世界：cast_spell, teleport, enchant...
```

**换世界 = 换 YAML。引擎 0 行改动。**

---

## 完整场景：杰洛特买草药

```
Tick N — 杰洛特:
  感官: 持有 金币×150 | 可用接口: take_out, hand_over, eat
  LLM: {physical_calls: [{interface:"hand_over", params:{entity:"金币",to:"托蜜拉",qty:15}}]}
  引擎: agent.interfaces["hand_over"] → delta(geralt,金币,-15) + spawn(pos=托蜜拉.pos,"杰洛特放下的金币")

Tick N+1 — 托蜜拉:
  感官: 视觉"杰洛特放下的金币(4格)" | 持有 金币×30
  LLM: {physical_calls: [{interface:"pick_up", params:{entity:"杰洛特放下的金币",qty:15}}]}
  引擎: delta(zone,金币,-15) + delta(托蜜拉,金币,+15) + despawn(金币实体)

引擎从不知"这是一笔交易" — 只执行了两次 MCP 调用。
```

---

## 快速开始

```bash
pip install -r requirements.txt
python main.py --validate-config
python main.py --runtime 60 --world config/world_trade.yaml   # 12 NPC 交易世界
python main.py --runtime 180 --world config/world.yaml        # 25 NPC Witcher
python -m pytest tests/ -q   # 177 tests, ~10s
```

---

## 设计原则

| 原则 | 体现 |
|---|---|
| 引擎报事实，LLM 做认知 | alias 事实映射。6 原语纯操作。LLM 从 tool list 决策 |
| 删除不添加 | 7→6 primitives。删 ops_registry、constraints、pocket entity |
| 零领域词 | 引擎代码只有 delta/spawn/despawn — 0 个世界名词 |
| YAML 驱动变体 | layer_registry、npc_interfaces、channels — 全 YAML 定义 |
| 引擎单入口 | `interact(entity, interface, params)` — 唯一 write 入口 |
| 世界绑定接口 | 物理接口在 YAML 里 — 换世界 = 换 tool list |
| 零 adapter | LLM 直接输出 MCP tool call — MCP 就是 adapter |

---

# English

## Core Concepts

### 1. Two-Layer Model

| | Spatial Layer | Abstract Layer |
|---|---|---|
| Responsibility | "Where / What it looks like" | "Who holds how many" |
| Storage | Memory (entities + SpatialGrid) | Memory edges + SQLite |
| Edges | None — physical adjacency | (src, tgt, qty) — untyped |
| Sensory | Visual / Auditory / Interactable | Inventory (NPC's 1-hop subgraph) |

NPCs and items share the same `Entity` class. `type_ref` links spatial entities to abstract `type_nodes`.

### 2. MCP Interface Model

Each NPC registers its supported interfaces in YAML. The LLM sees a tool list in its prompt and outputs tool calls directly.

```
Physical Layer:
  take_out({entity, qty})      Take from inventory into space
  hand_over({entity, to, qty}) Place item at target position
  eat({entity, qty})           Consume food
  pick_up({entity, qty})       Pick up from space into inventory

Abstract Layer:
  delta({src, tgt, qty})       Edge quantity change
  delta({entity, attr, value}) Attribute change
  spawn/despawn/relocate/add_node/remove_node
```

**The engine has a single entry point:** `interact()` routes to `agent.interfaces[name]` or `graph.primitives[name]`.

### 3. 6 Engine Primitives

| Primitive | Layer | Action |
|---|---|---|
| `delta` | Universal | Edge ± / Attribute ± |
| `spawn` | Spatial | Entity birth + visual + alias registration |
| `despawn` | Spatial | Entity death + alias cleanup |
| `relocate` | Spatial | Entity reposition |
| `add_node` | Abstract | Node enters edge system |
| `remove_node` | Abstract | Node leaves + edge cleanup |

Zero domain vocabulary in engine code. `take_out`, `eat`, `forge` live only in YAML and LLM prompts.

### 4. Channel-Driven Sensory

Sensor output is assembled by auto-registered channel source classes defined in YAML. Adding a channel = 1 YAML entry + 1 Python class — zero changes to `loop.py`.

### 5. Worlds Are Config Files

Swap worlds by swapping YAML. The same 6 primitives drive Witcher taverns or magic academies.

---

## Quick Start

```bash
pip install -r requirements.txt
python main.py --validate-config
python main.py --runtime 60 --world config/world_trade.yaml   # 12-NPC trade world
python main.py --runtime 180 --world config/world.yaml         # 25-NPC Witcher
python -m pytest tests/ -q   # 177 tests, ~10s
```

---

## Design Principles

| Principle | How |
|---|---|
| Engine reports facts, LLM decides | Alias registry is fact mapping. 6 primitives are pure ops. |
| Delete, don't add | 7→6 primitives. Removed ops_registry, constraints, pocket entities. |
| Zero domain vocab in engine | Only delta/spawn/despawn — zero world nouns. |
| YAML-driven variants | layer_registry, npc_interfaces, channels — all YAML config. |
| Single engine entry | `interact(entity, interface, params)` — sole write path. |
| World-bound interfaces | Physical interfaces in YAML — swap worlds, swap tool lists. |
| Zero adapter layer | LLM outputs MCP tool calls directly — MCP IS the adapter. |

---

## License

MIT
