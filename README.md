<p align="center">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue?style=flat-square">
  <img src="https://img.shields.io/badge/tests-176-brightgreen?style=flat-square">
  <img src="https://img.shields.io/badge/primitives-7-orange?style=flat-square">
  <img src="https://img.shields.io/badge/license-MIT-brightgreen?style=flat-square">
</p>

<h1 align="center">AgentWorld Async</h1>

<p align="center">
  <b>Two-Layer Architecture · MCP Interface Engine · 7 Primitives<br/>
  Engine reports facts. LLM provides cognition.<br/>
  <sub>双层架构 · MCP 接口引擎 · 7 原语 · 引擎报事实，LLM 做认知</sub></b>
</p>

---

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           LLM Layer (Cognition · 认知)                        │
│                                                                              │
│   Sensory channels: 视觉 / 听觉 / 可交互 / 持有                               │
│   MCP Tool List → LLM Decision (only physical interfaces + abs_attr_modify)   │
│   {  physical_calls: [{interface: "hand_over", params: {entity, to, qty}}],  │
│     abstract_calls:  [{interface: "abs_attr_modify", params: {entity, attr,  │
│                        value}}] }                                            │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ two-slot dispatch
┌───────────────────────────────▼──────────────────────────────────────────────┐
│                         MCP Engine (Routing · 路由)                            │
│                                                                              │
│   interact(entity, interface, params) — single write entry                    │
│   Inject caller context — validate params — route to handler                  │
│   Physical layer: agent.interfaces[name]    (world-bound YAML)                 │
│   Abstract layer: graph.primitives[name]    (expose_to_llm controlled)         │
│   Channel auto-registration · GraphSource · Alias Registry O(1)               │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
┌─────────▼──────────┐ ┌────────▼──────────┐ ┌────────▼──────────────────────┐
│  Spatial Layer     │ │  Abstract Layer   │ │  Interface Layer              │
│  (memory)          │ │  (edges/SQL)      │ │  (world-bound YAML)           │
│                    │ │                   │ │                               │
│  spatial_spawn     │ │ abs_holder_transfer│ │  npc_interfaces.yaml:          │
│  spatial_despawn   │ │ abs_attr_modify   │ │    take_out → hand_over → eat │
│  spatial_relocate  │ │ abs_node_add      │ │    pick_up (no direct transfer)│
│                    │ │ abs_node_remove   │ │                               │
│  Entities + pos    │ │                   │ │  npc_actions.py: impl           │
│  SpatialGrid       │ │ type_node × N     │ │  Item appears in space →       │
│  visual/auditory   │ │ edges: npc↔type   │ │    sensory → pick_up → done    │
│                    │ │        zone↔type   │ │  No npc↔npc direct transfer    │
└────────────────────┘ └───────────────────┘ └───────────────────────────────┘

  Single source of truth:  abstract_primitives.yaml  (expose_to_llm gates)
  World-bound config:       npc_interfaces.yaml           (physical tools)
  Layer attachment:         layer_registry.yaml            (YAML-driven)
  Channel definitions:      channels.yaml                  (auto-registered)
```

---

# 中文版

## 核心思想

### 1. 双层模型

| | 空间层 | 抽象层 |
|---|---|---|
| 职责 | "在哪 / 长什么样" | "谁持有多少" |
| 原语 | `spatial_spawn` / `despawn` / `relocate` | `abs_holder_transfer` / `abs_attr_modify` / `abs_node_add` / `abs_node_remove` |
| 感官 | 视觉 / 听觉 / 可交互 | 持有（npc 的一阶邻居子图） |

NPC 和物品是同一个 `Entity` class。`type_ref` 连接两层。

### 2. MCP 接口引擎

LLM 只能在 tool list 中看到暴露的接口。引擎原语对 LLM 不可见。

```
物理层（physical_calls — exposed to LLM）:
  take_out   · 从持有中拿出到空间
  hand_over  · 放到目标位置（不是转给某人——物品在空间中出现）
  eat        · 消耗食物
  pick_up    · 从空间中捡起走

抽象层（abstract_calls — exposed to LLM）:
  abs_attr_modify  · 自身属性变更（唯一暴露的抽象原语）

引擎原语（expose_to_llm: false — LLM 不可见）:
  abs_holder_transfer · 边数值转移
  spatial_spawn / despawn / relocate · 空间实体操作
  abs_node_add / abs_node_remove · 节点管理
```

### 3. 原则：物品必须先出现在空间中——禁止直接 NPC↔NPC 转账

```
A 拿出金币:   take_out → spawn("A 手中的金币") at A.pos
B 感官看到:   视觉: "A 手中的金币 (4 格)"
B 捡走:       pick_up("A 手中的金币") → despawn + 持有的边转移

永远没有: "A 直接把金币转给 B"
```

引擎不知道"交易"是什么——只知道实体在空间中诞生和消失。

### 4. 7 引擎原语

| 原语 | 层 | 做什么 |
|---|---|---|
| `abs_holder_transfer` | 抽象 | 边上数值转移。caller 验证：src 必须是 caller 自身或 zone |
| `abs_attr_modify` | 抽象 | 实体属性变更 |
| `spatial_spawn` | 空间 | 实体诞生——层附加通过 layer_registry YAML 驱动 |
| `spatial_despawn` | 空间 | 实体消失 + alias 清理 |
| `spatial_relocate` | 空间 | 实体改变位置 |
| `abs_node_add` | 抽象 | 节点加入边系统 |
| `abs_node_remove` | 抽象 | 节点脱离 + 关联边清理 |

### 5. YAML 驱动变体——全部

| 文件 | 内容 |
|---|---|
| `abstract_primitives.yaml` | 原语定义 + `expose_to_llm` 开关 |
| `item_registry.yaml` | 物品类型注册 |
| `layer_registry.yaml` | layer type → class 映射 + spawn 配置 |
| `npc_interfaces.yaml` | 物理接口注册（世界绑定） |
| `channels.yaml` | channel 定义 |
| `slot_groups.yaml` | slot 矩阵 + dimensions 列表 |

### 6. 单一事实来源

- 抽象原语定义：`abstract_primitives.yaml` — engine 加载 + LLM tool list 由此自动生成
- 物理接口定义：`npc_interfaces.yaml` — 切换世界观只需换此文件
- Prompt tool list：`{tool_list}` 占位符 — GraphSource 从 MCP Engine 自动生成

---

## 完整交易场景

```
Tick N — 杰洛特:
  感官: 持有 金币×80 草药×6
  LLM: {physical_calls: [{interface:"hand_over", params:{entity:"金币", to:"托蜜ラ", qty:15}}]}
  引擎: abs_holder_transfer(geralt, type_金币, -15, caller=geralt) ✅
        spatial_spawn(pos=tomerra.pos, "杰洛特放在托蜜ラ的金币")
        abs_holder_transfer(village, type_金币, +15)

Tick N+1 — 托蜜ラ:
  感官: 视觉 "杰洛特放在托蜜ラ的金币 (4 格)" | 持有 金币×30
  LLM: {physical_calls: [{interface:"pick_up", params:{entity:"杰洛特放在托蜜ラ的金币", qty:15}}]}
  引擎: abs_holder_transfer(village, type_金币, -15)
        abs_holder_transfer(tomerra, type_金币, +15)
        spatial_despawn("杰洛特放在托蜜ラ的金币")
```

---

## 快速开始

```bash
pip install -r requirements.txt
python main.py --validate-config
python main.py --runtime 60 --world config/world_trade.yaml   # 12 NPC 交易世界
python main.py --runtime 180 --world config/world.yaml         # 25 NPC Witcher
python -m pytest tests/ -q   # 176 tests, ~10s
```

---

## 设计原则

| 原则 | 体现 |
|---|---|
| 引擎报事实，LLM 做认知 | alias 事实映射。7 原语纯操作。LLM 从 tool list 决策 |
| 删除不添加 | 删 constraints 目录、ops_registry、pocket entity、r=-1 filter |
| 零领域词 | 引擎代码：abs_holder_transfer/spatial_spawn — 0 世界名词 |
| YAML 驱动变体 | 所有注册表均 YAML 定义——换世界 = 换 YAML |
| 引擎单入口 | `interact(entity, interface, params)` |
| 世界绑定接口 | 物理接口在世界 YAML 中——换世界 = 换 tool list |
| 物品先出现在空间 | 禁止直接 npc↔npc 持有层转账 |
| 单一事实来源 | `abstract_primitives.yaml` — engine + LLM tool list 同源 |

---

# English

## Core Concepts

### 1. Two-Layer Model

| | Spatial Layer | Abstract Layer |
|---|---|---|
| Responsibility | Where / What it looks like | Who holds how many |
| Primitives | `spatial_spawn/despawn/relocate` | `abs_holder_transfer/abs_attr_modify/abs_node_add/abs_node_remove` |
| Sensory | Visual / Auditory / Interactable | Inventory (NPC's 1-hop subgraph) |

### 2. MCP Interface Engine

LLM sees only exposed interfaces. Engine primitives are hidden.

```
Physical (exposed):  take_out · hand_over · eat · pick_up
Abstract (exposed):  abs_attr_modify  (only one)
Engine (hidden):     abs_holder_transfer · spatial_* · abs_node_*
```

### 3. Rule: Items must appear in space — no direct NPC↔NPC transfer

All item movement goes through spatial layer. A puts item down → B sees it → B picks it up. Never "A transfers directly to B."

### 4. 7 Engine Primitives

| Primitive | Layer | Action |
|---|---|---|
| `abs_holder_transfer` | Abstract | Edge quantity transfer with caller auth |
| `abs_attr_modify` | Abstract | Entity attribute modification |
| `spatial_spawn` | Spatial | Entity birth — layer attachment via YAML |
| `spatial_despawn` | Spatial | Entity death + alias cleanup |
| `spatial_relocate` | Spatial | Entity reposition |
| `abs_node_add` | Abstract | Node enters edge system |
| `abs_node_remove` | Abstract | Node leaves + edge cleanup |

### 5. YAML-Driven Configuration

All registries are YAML. Swap worlds = swap YAML files. `abstract_primitives.yaml` is the single source of truth for engine primitive definitions and LLM tool list generation.

---

## Quick Start

```bash
pip install -r requirements.txt
python main.py --validate-config
python main.py --runtime 60 --world config/world_trade.yaml   # 12-NPC trade world
python main.py --runtime 180 --world config/world.yaml         # 25-NPC Witcher
python -m pytest tests/ -q   # 176 tests, ~10s
```

---

## License

MIT
