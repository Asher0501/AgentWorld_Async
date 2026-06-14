<p align="center">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue?style=flat-square">
  <img src="https://img.shields.io/badge/tests-176-brightgreen?style=flat-square">
  <img src="https://img.shields.io/badge/license-MIT-brightgreen?style=flat-square">
</p>

<h1 align="center">AgentWorld Async</h1>

<p align="center">
  <b>A social emergence laboratory powered by LLMs.<br/>
  How much social behavior can arise when autonomous agents perceive only atomic facts<br/>
  — with no engine-level semantics, no priority hierarchies, no pre-programmed social rules?<br/>
  <sub>一个以 LLM 为实验对象的社会涌现实验室。<br/>
  当自主代理只能感知原子事实——没有引擎级语义、没有优先级体系、没有硬编码社交规则——<br/>
  能自发涌现多少社会行为？</sub></b>
</p>

---

## What This Is

This is not a game engine. It is not an agent framework. It is an experimental apparatus for studying one question:

> **Given a population of LLM-based autonomous agents embedded in a physical space with private goals and public resources — and an engine that refuses to interpret anything — what social structures, strategies, and emergent behaviors spontaneously arise from their interactions?**

The architecture is built around a single axiom: **the engine must never perform semantic compression.** All complex behavior — negotiation, social pressure, reciprocal exchange, attention allocation, loop detection — must be derived by the LLMs themselves from raw atomic facts, or it must not exist at all.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                            The Agent (LLM)                                  │
│                                                                            │
│  Every tick: read facts → complete 4-step cognitive pipeline → act          │
│                                                                            │
│  ┌─ Cognitive Pipeline (LLM must self-reflect — no defaults allowed) ────┐ │
│  │  ① goal             — What am I trying to achieve?                      │ │
│  │  ② perception       — What do I see, hear, sense right now?             │ │
│  │  ③ assessment       — How does my perception affect my goal?            │ │
│  │  ④ summary          — What has been happening recently? (detect loops)  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌─ Environment Facts (engine reports, never interprets) ────────────────┐ │
│  │  · 7 biological/social drives (hunger, social_pressure, ...)            │ │
│  │  · Spatial coordinates + traversable gates                              │ │
│  │  · Visual entities within radius                                        │ │
│  │  · Auditory speech with direction markers ("to you" / background)       │ │
│  │  · Inventory (held items via abstract edges)                            │ │
│  │  · Episodic memory buffer                                               │ │
│  │  · Last action feedback + conversation history                          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌─ Output Interface ────────────────────────────────────────────────────┐ │
│  │  Physical layer (exposed): take_out · hand_over · eat · pick_up         │ │
│  │  Abstract layer (exposed): abs_attr_modify (modify any drive value)     │ │
│  │  Engine primitives (hidden): holder_transfer · spawn/despawn · node ops │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                         The Engine (Zero Semantics)                          │
│                                                                            │
│  Never outputs: "trade completed", "A pressures B", "B owes A a response"  │
│  Only outputs:  numeric values, coordinates, timestamps, counts, entity IDs │
│                                                                            │
│  ┌─ Spatial  ─── entity positions, zone grids, visual/auditory layers       │
│  ├─ Abstract ── ownership edges (holder → item_type → qty)                  │
│  ├─ Drive   ─── decaying attributes: hunger, thirst, social, mood,          │
│  │              social_pressure (+0.05/min), energy, fun                     │
│  └─ Sensory ─── radius-based perception: who is nearby, who spoke,          │
│                 with speech_target → direction label injection              │
│                                                                            │
│  YAML-defined layers · channel auto-registration · alias registry O(1)      │
│  7 primitives · MCP routing (zero op-name branching) · single source of truth│
└────────────────────────────────────────────────────────────────────────────┘
```

**Key constraint**: The cognitive pipeline slots and drive values are the ONLY channels through which the LLM perceives the world. No slot carries a "priority" annotation — the LLM must decide what matters. No drive value comes with an instruction — the LLM must derive appropriate responses from numeric signals alone.

---

## Core Axiom: The Engine Must Never Perform Semantic Compression

The engine knows what coordinates changed, what numbers incremented, who spoke to whom. It does not know — and must not be told — what any of these facts *mean*.

| Engine Reports (Atomic Fact) | LLM Must Derive (Cognitive Interpretation) |
|---|---|
| `hunger: 85/100` | "I need food" |
| `social_pressure: 75/100` | "Someone is pressuring me repeatedly" |
| `speech_target = this_agent_id` | "That person is speaking to me" |
| Coins appear at position X via spawned entity | "I was paid" |
| `memory_analysis` repeats same pattern across 10 ticks | "I am stuck in a negotiation loop" |
| Other agent's `quest_analysis` text (visible to no one) | (Not perceivable — each agent's cognition is private) |

This is the **only** invariant enforced across the entire codebase. Every other design decision — flat-priority prompts, direction markers, social_pressure as a drive, the cognitive pipeline — is a derived consequence of refusing to let the engine perform this compression.

### What "semantic compression" means concretely

If the engine ever produced the string `"Geralt is pressuring Tomera"`, it would have compressed three atomic facts — (a) Geralt spoke with target=Tomera, (b) this happened 25 times, (c) Tomera has not responded — into a single interpretive label. The LLM would then reason about the *label*, not the *facts*. The experimental value of the system is destroyed at the moment of compression.

---

## Why This Architecture Is Interesting

### 1. No pre-programmed social rules

There is no code path that says "if someone speaks to you, you should respond." There is no reputation system. No obligation tracking. No social graph maintenance by the engine. All social behavior — including reciprocal exchange, sustained negotiation, and persistent ignoring — emerges purely from LLMs reading their own cognitive pipeline history alongside raw environmental facts.

### 2. The LLM is the sole interpreter

Every drive value, every sensory input, every piece of feedback — the LLM must interpret them all without help. The `social_pressure` attribute could mean "I am being interrogated" or "I feel guilty about ignoring someone" or "the crowd is loud today." The engine has no opinion on which interpretation is correct.

### 3. Emergent social phenomena have been observed

| Phenomenon | Description | Mechanism |
|---|---|---|
| Symmetric negotiation deadlock | Two agents independently converge to "respond first, then push my agenda" — producing a 33-round stalemate | Both read the same cognitive pipeline → both derive same strategy → neither breaks symmetry |
| Strategy escalation | An agent evolves from "ask for a free story" to "pay gold for a story" across 11 rounds with no "buy story" interface | LLM constructs novel use of `hand_over` primitive |
| Reciprocal intelligence exchange | Agents exchange non-monetary information as a byproduct of a completed trade | No code enforces reciprocity — it self-organizes |
| Pressure-independent behavior | Social pressure values rise to 100 with zero behavioral change — the LLM perceives but doesn't necessarily respond to numeric pressure alone | Drive values are signals, not commands |

### 4. The cognitive pipeline forces explicitness

The LLM cannot silently ignore a sensory input. It must write — every tick — what it perceives, how that perception affects its goal, and what has been happening recently. If it chooses to ignore someone, that choice is recorded in explicit text that the LLM itself re-reads next tick. The pipeline turns implicit neglect into explicit, revisable cognition.

---

## Concrete Example: How a Conversation Works

```
Tick N:
  Geralt's LLM writes:  action = "walk toward Tomera"
                         dialogue = "Have you seen Yennefer?"
                         target_name = "Tomera"
  Engine at flush:       → writes speech_target = "Tomera" to Geralt's auditory layer
                         → writes dialogue to Geralt's auditory layer

Tick N+1:
  Tomera's prompt renders:
    ## 感知 (sensory_analysis — LLM reads its own previous analysis)
    ## 听觉
    杰洛特 (3s前) 对你说: "Have you seen Yennefer?"
    ## 评估 (quest_analysis — LLM writes)
    "Geralt is looking for Yennefer, a sorceress. He is a witcher —
     his sorceress contact could be the herb buyer I need.
     If I ignore him now, I may lose this lead."

  Tomera's LLM writes:   action = "turn to face Geralt"
                         dialogue = "I've heard of her. She was in Novigrad."
```

No engine component ever decided that Tomera "should" respond. The `"对你说"` marker was injected mechanically — `SensoryMemory.to_prompt()` compared `speech_target` with the observer's name and appended a string. The quest analysis text was written by the LLM itself in the previous tick. The decision to engage was entirely the LLM's.

---

## Quick Start

```bash
pip install -r requirements.txt
python main.py --validate-config             # validate YAML configs
python main.py --runtime 180 \
    --world config/world_trade.yaml          # 12-NPC trade world, 180s
python -m pytest tests/ -q                   # 176 tests, ~10s
```

---

## 这是什么

这不是游戏引擎，也不是 agent 框架。这是一个实验装置，用来研究一个问题：

> **当一群基于 LLM 的自主代理被嵌入物理空间，各自持有私有目标和公共资源——并且引擎拒绝做任何语义解释时——它们的交互中能自发涌现出怎样的社会结构、策略和行为？**

整个架构围绕一条公理构建：**引擎不得进行语义压缩。** 所有复杂行为——谈判、社交压力、互惠交换、注意力分配、loop 检测——必须由 LLM 自己从原始原子事实中推导出来，否则就不存在。

## 架构

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         代理 (LLM)                                          │
│                                                                            │
│  每轮: 读取事实 → 完成 4 步认知管道 → 行动                                    │
│                                                                            │
│  ┌─ 认知管道 (LLM 必须自省 — 不允许默认文本) ─────────────────────────────┐ │
│  │  ① 目标     — 我要达成什么？                                             │ │
│  │  ② 感知     — 我现在看到了什么、听到了什么？                                │ │
│  │  ③ 评估     — 感知如何影响我的目标？                                      │ │
│  │  ④ 总结     — 最近发生了什么？（检测重复模式）                              │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌─ 环境事实 (引擎报，绝不解释) ──────────────────────────────────────────┐ │
│  │  · 7 个生物/社交驱动 (饥饿, 社交压力, ...)                                │ │
│  │  · 空间坐标 + 可穿越的门                                                  │ │
│  │  · 视觉范围内的实体                                                       │ │
│  │  · 听觉对话 + 方向标记 ("对你说" / 背景)                                   │ │
│  │  · 持有物 (抽象层边)                                                       │ │
│  │  · 情景记忆缓冲                                                           │ │
│  │  · 上轮行动反馈 + 对话历史                                                 │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌─ 输出接口 ────────────────────────────────────────────────────────────┐ │
│  │  物理层 (暴露): take_out · hand_over · eat · pick_up                     │ │
│  │  抽象层 (暴露): abs_attr_modify (修改任意驱动值)                           │ │
│  │  引擎原语 (隐藏): holder_transfer · spawn/despawn · node ops             │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                       引擎 (零语义)                                          │
│                                                                            │
│  从不说: "交易完成", "A在施压B", "B欠A一个回应"                               │
│  只说:   数值, 坐标, 时间戳, 计数, 实体ID                                    │
│                                                                            │
│  ┌─ 空间层  ── 实体位置, 区域网格, 视觉/听觉层                                │
│  ├─ 抽象层  ── 所有权边 (holder → item_type → qty)                          │
│  ├─ 驱动层  ── 衰减属性: hunger, thirst, social, mood,                      │
│  │            social_pressure (+0.05/min), energy, fun                      │
│  └─ 感官系统 ── 半径感知 + speech_target → direction label 注入              │
│                                                                            │
│  YAML定义层 · channel自动注册 · alias注册表O(1)                              │
│  7原语 · MCP路由(零 op-name 分支) · 单一事实来源                                │
└────────────────────────────────────────────────────────────────────────────┘
```

## 核心公理：引擎不得进行语义压缩

引擎知道什么坐标变了、哪个数值涨了、谁对谁说了话。引擎不知道——也不能被告知——这些事实*意味着*什么。

| 引擎报 (原子事实) | LLM 必须推导 (认知解释) |
|---|---|
| `hunger: 85/100` | "需要进食" |
| `social_pressure: 75/100` | "有人在反复对我施压" |
| `speech_target = 此 agent 的 ID` | "那个人在对我说重要的话" |
| 金币通过 spawn 实体出现在坐标 X | "他付了钱" |
| `memory_analysis` 连续 10 轮同样模式 | "我 stuck 在谈判 loop 里了" |
| 其他 agent 的 `quest_analysis`（无人可见） | （不可感知——每个 agent 的认知是私有的） |

### "语义压缩"具体指什么

如果引擎产出了字符串 `"杰洛特在施压托蜜拉"`，它就把三个原子事实——(a) 杰洛特对托蜜拉说了话，(b) 说了 25 次，(c) 托蜜拉没回应——压缩成了一个解释性标签。LLM 接下来就会推理这个*标签*，而不是推理*事实*。压缩发生的那一刻，整个系统的实验价值就没了。

## 为什么这个架构有价值

### 1. 零硬编码社交规则

代码里没有任何地方说"如果别人对你说话，你就该回应"。没有声誉系统、没有义务追踪、没有引擎维护的社交图。所有社会行为——互惠、持续谈判、持续性忽视——全都是 LLM 读自己认知管道历史 + 原始环境事实后自发产生的。

### 2. LLM 是唯一的解释者

每个驱动值、每条感官输入、每条反馈——LLM 都必须自己解释。`social_pressure` 这个属性可以意味着"我被审问了"，也可以是"我因为忽视了某个人而感到内疚"，也可以是"今天市场太吵了"。引擎不对哪个解释是正确的发表意见。

### 3. 已观测到涌现社会现象

| 现象 | 描述 | 机制 |
|---|---|---|
| 对称谈判僵局 | 两个 agent 同时收敛到"先回应对方再推自己目标"——产生 33 轮僵局 | 两人读到同一个认知管道 → 推导同一策略 → 无人打破对称 |
| 策略升级 | 一个 agent 从"求免费故事"进化到"出金币买故事"，跨 11 轮 | LLM 自创了 `hand_over` 原语的新用法 |
| 互惠情报交换 | agent 在完成矿石交易后额外交换了非货币情报 | 无代码强制互惠——自组织产生 |
| 压力-行为脱钩 | social_pressure 涨到 100 而行为没变——LLM 感知到但不一定响应 | 驱动值是信号，不是命令 |

### 4. 认知管道强制显式化

LLM 不能默默忽视一条感官输入。它必须写——每轮都写——感知到了什么、感知如何影响目标、最近发生了什么。如果它选择忽视某人，这个选择被记录为一段显式文本，LLM 自己下轮会重新读到。管道把隐性忽视变成了显性的、可修正的认知。

---

## 具体例子：对话如何工作

```
Tick N:
  杰洛特 LLM 写:    action = "走向托蜜拉"
                    dialogue = "你见过叶奈法吗？"
                    target_name = "托蜜拉"
  引擎 flush 时:     → 将 speech_target = "托蜜拉" 写入杰洛特的 auditory 层
                    → 将 dialogue 写入杰洛特的 auditory 层

Tick N+1:
  托蜜拉 prompt 渲染:
    ## 感知
    ## 听觉
    杰洛特 (3s前) 对你说: "你见过叶奈法吗？"
    ## 评估 (quest_analysis — LLM 自己写)
    "杰洛特在问叶奈法，她是女术士——他的术士联系人
     可能就是我需要的草药买家。如果无视他，可能失去这条线。"

  托蜜拉 LLM 写:    action = "转向杰洛特"
                    dialogue = "听说过。她在诺维格瑞出现过。"
```

没有任何引擎组件决定托蜜拉"应该"回应。`"对你说"` 标记是机械注入的——`SensoryMemory.to_prompt()` 比较了 `speech_target` 和 observer 的名字，追加了一个字符串。quest_analysis 文本是 LLM 自己上轮写的。回应的决定完全是 LLM 的。

---

## Quick Start

```bash
pip install -r requirements.txt
python main.py --validate-config
python main.py --runtime 180 --world config/world_trade.yaml
python -m pytest tests/ -q       # 176 tests
```

---

## License

MIT
