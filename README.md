<p align="center">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue?style=flat-square">
  <img src="https://img.shields.io/badge/async-asyncio-purple?style=flat-square">
  <img src="https://img.shields.io/badge/LLM-DeepSeek%20%7C%20MiniMax-green?style=flat-square">
  <img src="https://img.shields.io/badge/tests-159-brightgreen?style=flat-square">
  <img src="https://img.shields.io/badge/license-MIT-brightgreen?style=flat-square">
</p>

<h1 align="center">AgentWorld Async</h1>

<p align="center">
  <b>Engine provides facts. LLM provides cognition.<br/>World unchanged, Agent unmoved.</b>
</p>

---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             main.py  (CLI Entry)                            │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
           ┌──────────────┐ ┌─────────────┐ ┌──────────────┐
           │  Core/World  │ │ Agent Loop  │ │ LLM+Prompts  │
           │              │ │ (loop.py)   │ │              │
           │ World/Entity │ │ Sense       │ │ LLMClient    │
           │ SpatialGrid  │ │   |         │ │ Concur.Gate  │
           │ Clock        │▶│ Delta Gate  │▶│ Assembler    │
           │ Lifecycle    │ │   |         │ │ 14-Slot      │
           │ Director     │ │ Decide(LLM) │ │ safe_format  │
           │ Session      │ │   |         │ └──────────────┘
           └──────────────┘ │ Act         │
                            │   |         │ ┌──────────────┐
           ┌──────────────┐ │ Flush       │ │ Agent State  │
           │   Systems    │ │             │ │ (layers/)    │
           │ Sensory      │▶│ P/Q State   │▶│ AgentLayer   │
           │ Interaction  │ │ Write Lock  │ │ Drives       │
           │ Decay        │ │ err_backoff │ │ Memory(10)   │
           └──────────────┘ └─────────────┘ │ SensoryMem   │
                                            └──────────────┘
     ┌────────────┬──────────────┐
     ▼            ▼              ▼
┌──────────┐ ┌──────────┐ ┌──────────────┐    ┌─────────────────┐
│Event Bus │ │ Director │ │ Error+Logger │    │  Channel System │
│register  │ │freeze    │ │ logger/      │    │  (config YAML)  │
│emit WS   │ │take      │ │ 6 hooks      │    │                 │
│history   │ │order     │ │ SQLite       │    │ agent_layer     │
│unregister│ │snap      │ │ dedup/dump   │    │ world  drives   │
└──────────┘ └──────────┘ └──────────────┘    │ sensory memory  │
     │                                        │ traits delta    │
  ┌──┴───────┐                                 │ collect(ctx) →  │
  ▼          ▼                                 └─────────────────┘
┌──────┐ ┌──────┐ ┌──────────────┐
│Dash. │ │Visual│ │ Gateway API  │ ┌──────────────┐ ┌───────────┐
│:8766 │ │:8767 │ │ join/perceive│ │   AutoGenSim │ │   Eval    │
│ WS   │ │PixiJS│ │ act/leave    │ │   team<>NPC  │ │ 18 metrics│
│监控  │ │像素  │ │ REST+WS      │ │   Director   │ │ 5 cats    │
└──────┘ └──────┘ └──────────────┘ └──────────────┘ └───────────┘
```

---

# 中文版

## 五个核心思想

### 1. 引擎报告，LLM 判断

引擎不教 agent 怎么做。引擎只报告事实：`mood=5`、gate 存在、`target_name` 匹配成功。不说"心情很差"、不说"应该穿越"。全部认知判断权在 LLM，通过 YAML slot 组合引导。

### 2. 声明式认知架构 — 14 Slot，3 层

Generative Agents 的 730 行认知代码 → 14 个 YAML slot + 45 行字符串格式化引擎。三层：
- **Contract** — 输出契约 (`action_scope` / `output_contract`)
- **World** — 环境事实 (`delta_gate` / `spatial` / `sensory` / `gate_highlight`)
- **NPC** — 角色驱动 (`persona` / `main_thread` / `drive_values` / `drive_context` / `memory` / `conversation` / `traits` / `intent_context`)

`slot_groups.yaml` 二维矩阵控制 per-agent slot 激活。新认知 = 加一行 YAML。零 Python 改动。

### 3. P/Q Delta Gate — 世界不变，Agent 不动

Agent 维护内部世界模型 P，每帧对比感官 Q。P=Q → 零 LLM 调用。P≠Q → 触发决策。四通道并行 diff。发呆不花钱。Token 节省 2/3。

### 4. Channel-Driven Architecture

**loop.py 不做格式化。** ctx dict 的每个 key 由 YAML 定义的 channel 驱动。8 个 channel 对应 7 个数据源——loop.py 只管 `channel.collect(ctx)`，不格式化、不命名、不解释。

```
config/channels.yaml         src/channel.py              ctx dict
───────────────────          ─────────────               ───────
- source: agent_layer  →  AgentLayerSource.collect()  → personality, main_thread
- source: world        →  WorldSource.collect()       → zone_name, pos_x, gate_text
- source: drives       →  DriveSource.collect()       → drives_table, drive_min/max
- source: sensory      →  SensorySource.collect()     → sensory_text
- source: memory       →  MemorySource.collect()      → memory_text
- source: traits       →  TraitsSource.collect()      → traits_text
- source: delta_gate   →  DeltaGateSource.collect()   → delta_text
```

**新增 channel = YAML 加 3 行。零 Python change。**

### 5. 世界观即配置

换世界 = 换 YAML 文件。同一引擎驱动猎魔人酒馆、老友记咖啡厅。属性名相同 → prompts.yaml 一字不改。Gateway REST/WebSocket 接口——外部 agent 通过 `join/perceive/act` 与自主 agent 共享同一决策通道。

---

## vs. Generative Agents

```
                         SVA (AgentWorld)              Generative Agents
                         ────────────────              ──────────────────
  Cognitive Code         45 lines Python               730 lines Python
  LLM Triggers           Change-detected (P/Q gate)    Every tick
  Token Usage            -67%                          Baseline (1x)
  New Behavior           Add 1 YAML channel            Rewrite Python functions
  World Swap             1 YAML file                   Rewrite code
  Tests                  159 automated                 Manual only
  External Control       Director freeze/take/order    None
  Observability          Logger (6 hooks, SQLite)      None
```

---

## 实证 (v12, 7 Agents, 180s, Friends)

| 指标 | 数值 |
|------|------|
| 总行动 | **142** |
| 对话率 | **100%** (142/142) |
| NPC↔NPC 率 | **100%** |
| 行动多样性 | **92%+** |
| Token 优化 | **-67%** |

---

## 快速开始

```bash
pip install -r requirements.txt
python main.py --validate-config
python main.py --demo --world config/world_friends.yaml
python main.py --runtime 180 --validate --output data/traces/trace.json
python main.py --eval-report data/traces/trace.json
python -m pytest tests/ -q     # 159 tests, ~10s
```

---

## 版本

| Ver | 里程碑 |
|-----|--------|
| **v13** | Channel-driven architecture · Logger 6-hook · 删除 error_collector |
| **v12** | 三层 slot 组 · slot_groups 矩阵 · per-agent traits · intent_context |
| **v11** | target_name 精确匹配 · Director · Gateway API · 159 测试 |
| **v10-v4** | 多世界热切换 · drive · gate crossing · sensory · P/Q gate |

---

# English

## Five Principles

### 1. Engine Reports Facts, LLM Decides

The engine prescribes nothing. It reports `mood=5`, gate exists, `target_name` matched. Not "you are depressed," not "you should cross zones." All cognition emerges from LLM judgment, guided by YAML slot composition.

### 2. Declarative Cognitive Architecture — 14 Slots, 3 Layers

Generative Agents' 730 lines of cognitive Python → 14 YAML slots + 45-line string formatter.

### 3. P/Q Delta Gate — No Change, No Thought

Agent maintains internal world model P, compares to sensory input Q each tick. P=Q → zero LLM calls.

### 4. Channel-Driven Architecture

**loop.py does zero formatting.** Each ctx key is driven by a YAML-defined channel. 8 channels map to 7 data sources. loop.py only calls `channel.collect(ctx)` — no formatting, no naming, no interpretation. New channel = 3 lines of YAML.

### 5. Worlds Are Config Files

Swap worlds by swapping YAML files. Same engine drives The Witcher tavern, Friends coffee shop.

---

## Quick Start

```bash
pip install -r requirements.txt
python main.py --validate-config
python main.py --demo --world config/world_friends.yaml
python main.py --runtime 180 --validate --output data/traces/trace.json
python -m pytest tests/ -q     # 159 tests, ~10s
```

---

## License

MIT
