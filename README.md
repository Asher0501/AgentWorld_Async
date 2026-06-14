<p align="center">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue?style=flat-square">
  <img src="https://img.shields.io/badge/tests-176-brightgreen?style=flat-square">
  <img src="https://img.shields.io/badge/license-MIT-brightgreen?style=flat-square">
</p>

<h1 align="center">AgentWorld Async</h1>

<p align="center">
  <b>A social emergence laboratory powered by LLMs.<br/>
  <sub>一个以 LLM 为实验对象的社会涌现实验室。</sub></b>
</p>

<p align="center"><b>
  How much social behavior can arise when autonomous agents perceive<br/>
  only atomic facts — with no engine-level semantics, no priority<br/>
  hierarchies, no pre-programmed social rules?<br/>
  <sub>当自主代理只能感知原子事实——没有引擎级语义、没有优先级体系、<br/>
  没有硬编码社交规则——能自发涌现多少社会行为？</sub>
</b></p>

---

## Core Idea · 核心思想

```
All AI agent frameworks today work the same way:
   The developer writes domain logic. The engine knows what "trade" means.
   The agent is a thin wrapper around an LLM with pre-defined tools.

This project inverts that:
   The engine knows nothing. It only reports numbers, coordinates, timestamps.
   The LLM is the sole interpreter. All semantics must be derived at runtime.
```

```
今天所有的AI agent框架都一个模式：
   开发者写领域逻辑。引擎知道"交易"是什么意思。
   Agent 只是 LLM + 预定义工具的薄壳。

本项目将这个模式反转：
   引擎一无所知。只报数值、坐标、时间戳。
   LLM 是唯一的解释者。所有语义必须在运行时推导。
```

> **Axiom · 公理: The engine must never perform semantic compression.**
> **引擎不得进行语义压缩。**

There is exactly one invariant enforced across the entire codebase. Every other design decision
falls out of it as a corollary.

整个代码库只强制一条不变量。所有其他设计决定都是它的推论。

---

## Architecture · 架构

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         THE AGENT (LLM — SOLE INTERPRETER)                 │
│                         代理 (LLM — 唯一解释者)                              │
│                                                                            │
│  ┌─── COGNITIVE PIPELINE (4-step self-reflection, every tick) ───────────┐│
│  │   认知管道 (4步自省, 每轮强制)                                           ││
│  │                                                                        ││
│  │   ① goal        What am I trying to achieve? · 我要达成什么？            ││
│  │   ② perception  What do I see/hear right now? · 我此刻感知到什么？        ││
│  │   ③ assessment  How does perception affect my goal? · 感知如何影响目标？  ││
│  │   ④ summary     What has been happening recently? · 最近发生了什么？      ││
│  └──────────────────────────────────────────────────────────────────────┘│
│                                                                            │
│  ┌─── ENVIRONMENT FACTS (engine reports, never interprets) ──────────────┐│
│  │   环境事实 (引擎报, 绝不解释)                                              ││
│  │                                                                        ││
│  │   7 drives:    hunger · thirst · social · energy · fun · mood           ││
│  │                social_pressure (peer to hunger — engine decay only)    ││
│  │   Spatial:     coordinates · zone gates                                ││
│  │   Visual:      entities within radius                                  ││
│  │   Auditory:    speech + direction marker ("to you" / background)       ││
│  │   Inventory:   held items (abstract edges)                             ││
│  │   Memory:      episodic buffer · conversation history                  ││
│  └──────────────────────────────────────────────────────────────────────┘│
│                                                                            │
│  ┌─── OUTPUT INTERFACE ──────────────────────────────────────────────────┐│
│  │   输出接口                                                                ││
│  │                                                                        ││
│  │   Physical (exposed): take_out · hand_over · eat · pick_up             ││
│  │   Abstract (exposed): abs_attr_modify (modify any drive)              ││
│  │   Engine primitives (hidden): holder_transfer · spawn/despawn · node  ││
│  └──────────────────────────────────────────────────────────────────────┘│
└───────────────────────────────┬────────────────────────────────────────────┘
                                │  two-slot dispatch · 双槽路由
┌───────────────────────────────▼────────────────────────────────────────────┐
│                           THE ENGINE (ZERO SEMANTICS)                       │
│                           引擎 (零语义)                                       │
│                                                                             │
│   Never says: "trade completed" · "A pressures B" · "B ignores A"          │
│   从不说: "交易完成" · "A 在施压 B" · "B 忽视了 A"                             │
│                                                                             │
│   ┌─ Spatial  ─ entity positions · zone grids · visual/auditory layers     ││
│   │            空间层                                                         ││
│   ├─ Abstract ─ ownership edges (holder → item_type → qty)                 ││
│   │            抽象层                                                         ││
│   ├─ Drive   ── 7 decaying attributes + per-attr LLM-written notes         ││
│   │            驱动层                                                         ││
│   └─ Sensory ── radius-based perception · speech_target → direction label  ││
│                感官系统                                                       ││
│                                                                             │
│   YAML-defined layers · channel auto-registration · alias registry O(1)     │
│   7 primitives · MCP routing (zero op-name branching)                       │
│   Single source of truth: abstract_primitives.yaml                          │
└────────────────────────────────────────────────────────────────────────────┘
```

### What "No Semantic Compression" Means · "不进行语义压缩"的含义

If the engine ever produced the string `"Geralt is pressuring Tomera"`,
it would have compressed three atomic facts into one interpretive label.
The LLM would then reason about the *label*, not the *facts*.

如果引擎产出了 `"杰洛特在施压托蜜拉"`，它就把三个原子事实压缩成了一个标签。
LLM 就会推理这个*标签*，而不是推理*事实*。

```
Atomic Facts (引擎知道的事)          Compressed Label (绝不能产出)
─────────────────────────────       ─────────────────────────
(a) Geralt spoke × target=Tomera    "Geralt is pressuring Tomera"
(b) This happened 25 times          "杰洛特在施压托蜜拉"
(c) Tomera has not responded
```

The experimental value of the system is destroyed at the moment of semantic compression.
系统的实验价值在语义压缩发生的那一刻就被摧毁了。

---

## Key Mechanisms · 核心机制

### 1. The Cognitive Pipeline · 认知管道

```
Every tick, the LLM must pass through 4 fixed self-reflection steps.
No default text. No skipping.

每轮 LLM 必须经过 4 步固定自省。不允许默认文本。不允许跳过。

                          LLM writes:           Engine does:
                             LLM 写:              引擎:
  ┌─ goal ───────────┐  "Find the sorceress"    Store text · 存文本
  │ 目标              │  "找术士买家"
  ├─ perception ─────┤  "Geralt nearby. He      Store text · 存文本
  │ 感知              │   said 'Where is Yen?'"
  ├─ assessment ─────┤  "If I ignore him, I     Store text · 存文本
  │ 评估              │   lose a lead. Respond."
  ├─ summary ────────┤  "Asked him 10 times.    Store text · 存文本
  │ 总结              │   Same response. Stuck?"
  └──────────────────┘
         │
         ▼
  LLM decides action · LLM 决定行动
```

The pipeline is mounted BEFORE all environment facts in the prompt.
The LLM must see its own previous reflection before seeing new sensory input.
认知管道排在所有环境事实之前。LLM 必须先看到自己上轮的反思，再看到新的感官输入。

### 2. Drive System · 驱动系统

```
7 attributes, all peer-equal. social_pressure is modeled identically to hunger.

7 个属性, 全平级。social_pressure 与 hunger 使用完全相同机制。

  Engine decays:       LLM can modify via abs_attr_modify:
  引擎衰减:             LLM 可通过 abs_attr_modify 修改:

  hunger    +0.018/min       "I ate" → abs_attr_modify(hunger, -20)
  social_pressure +0.05/min  "I responded" → abs_attr_modify(social_pressure, -15)
                              "Being interrogated" → abs_attr_modify(social_pressure, +20)

  ┌─────────────┬──────────┬──────────┬─────────────────────────────┐
  │ Attribute   │ Value    │ Engine   │ LLM-written Feeling · LLM写 │
  │ 属性         │ 值       │ Decay    │                              │
  ├─────────────┼──────────┼──────────┼─────────────────────────────┤
  │ thirst      │ 55/100   │ +0.022   │ "有点渴"                     │
  │ hunger      │ 85/100   │ +0.018   │ "饿得胃疼, 得赶紧吃"            │
  │ social      │ 20/100   │ +0.015   │ "想和人聊聊天"                 │
  │ energy      │ 85/100   │ −0.01    │                               │
  │ fun         │ 15/100   │ +0.015   │                               │
  │ mood        │ 50/100   │ 0.0      │                               │
  │ social_pressure│75/100│ +0.05    │ "杰洛特在等我回答, 有点着急"       │
  └─────────────┴──────────┴──────────┴─────────────────────────────┘

No drive value comes with a behavioral instruction.
The LLM must derive: "hunger: 85 → should eat", "social_pressure: 75 → should respond".

没有任何驱动值附带行为指令。
LLM 必须自己推导: hunger: 85 → 该吃饭了, social_pressure: 75 → 该回应了。
```

### 3. Direction Markers · 方向标记

```
When an NPC speaks, the engine stores `speech_target` alongside the dialogue.
At sensory render time, this is mechanically injected into the text.
No semantic interpretation. Pure label injection.

当 NPC 说话时, 引擎存储 `speech_target` 与对话内容。
渲染感官时, 机械注入方向标签。零语义解释。纯字符串追加。

  Engine stores:                  Sensory render for observer Tomera:
  引擎存储:                        对观察者托蜜拉的感官渲染:

  auditory.properties = {         ┌─────────────────────────────────┐
    current_speech: "Where is     │ ## 听觉                         │
                     Yennefer?"   │ 杰洛特 (3s前) 对你说:            │
    speech_target:   "Tomera"     │   "Where is Yennefer?"          │
  }                               │                                 │
                                  │ 莎拉 (12s前):                    │ ← no "对你说"
  SensoryMemory.to_prompt():      │   "今天天气不错"                   │    background
    if speech_target == obs_name  │                                 │    speech
      → inject "对你说"           └─────────────────────────────────┘
    else                          
      → inject ""
```

### 4. MCP Engine · MCP 引擎

```
Zero op-name branching. Zero domain vocabulary in engine code.
Physical interfaces: YAML-defined, world-bound.
Abstract primitives: YAML-defined, expose_to_llm gating.

零 op-name 分支。零领域词汇。物理接口: YAML 定义, 世界绑定。
抽象原语: YAML 定义, expose_to_llm 门控。

  MCP.route({"physical": [...], "abstract": [...]}, agent=agent, world=world)
    │
    ├─ physical calls → agent.interfaces[name]    (npc_actions.py)
    │     take_out · hand_over · eat · pick_up
    │
    └─ abstract calls → graph.primitives[name]    (graph.py)
          Only abs_attr_modify exposed to LLM.
          Engine-internal: holder_transfer · spawn/despawn · node_add/remove
```

---

## Emergent Phenomena · 涌现现象

All observed in 180-second simulation runs with 12 NPCs. No behavior was pre-programmed.
全部在 12-NPC 180 秒模拟中观测到。无行为是预编程的。

| Phenomenon · 现象 | Description · 描述 | Mechanism · 机制 |
|---|---|---|
| **Symmetric negotiation deadlock**<br/>对称谈判僵局 | Two agents independently converge to the same strategy ("respond first, then push my agenda"), producing a 33-round stalemate.<br/>两个 agent 独立收敛到同一策略("先回应再推自己"), 产生 33 轮僵局 | Both read identical cognitive pipeline structure → both derive same meta-strategy → neither breaks symmetry<br/>两人读到相同的认知管道结构 → 推得相同策略 → 无人打破对称 |
| **Strategy escalation**<br/>策略升级 | Dandelion evolves from "ask for a free story" to "pay gold for a story" across 11 rounds. No "buy story" interface exists.<br/>丹德里恩 从"免费要故事"进化到"出金币买故事"跨 11 轮。系统里没有"买故事"接口。 | LLM constructs novel use of `hand_over` primitive to transfer coins as story payment<br/>LLM 自创 `hand_over` 的新用法 |
| **Reciprocal exchange**<br/>互惠交换 | Zoltan and Hattori exchange non-monetary intelligence as a byproduct of a completed ore trade.<br/>卓尔坦和哈托里完成矿石交易后自发性交换了非货币情报。 | No code enforces reciprocity — it self-organizes<br/>无代码强制互惠——自组织产生 |
| **Pressure-behavior decoupling**<br/>压力-行为脱钩 | Social pressure value reaches 100 with zero behavioral change. The LLM perceives the number but does not necessarily respond.<br/>社交压力涨到 100 行为不变。LLM 感知到数字但不一定响应。 | Drive values are signals, not commands. The LLM retains autonomy over interpretation.<br/>驱动值是信号, 不是命令。LLM 保留解释自主权。 |

---

## Comparison with Similar Projects · 与同类项目的区别

| Dimension · 维度 | Typical Agent Framework<br/>典型 Agent 框架 | AgentWorld Async |
|---|---|---|
| **Semantic ownership**<br/>语义主权 | Developer writes "when hungry, find food." Engine knows what "hungry" means.<br/>开发者写"饿了就找吃的"。引擎知道"饿"是什么意思。 | Engine only reports `hunger: 85`. LLM must decide what "85" means and what to do.<br/>引擎只报 `hunger: 85`。LLM 自己决定"85"意味着什么、该做什么。 |
| **Social rules**<br/>社交规则 | Hardcoded: "if spoken to, respond." Reputation systems, obligation tracking built into engine.<br/>硬编码: "如果别人对你说话, 就回应"。声誉系统、义务追踪内置于引擎。 | Zero hardcoded social rules. All social behavior emerges from LLMs reading facts.<br/>零硬编码社交规则。所有社交行为从 LLM 读事实中涌现。 |
| **Priority system**<br/>优先级体系 | Hand-tuned weights: main quest > survival > social. Static hierarchy.<br/>手调权重: 主线 > 生存 > 社交。静态层级。 | Flat-priority: all slots equal. LLM allocates attention autonomously each tick.<br/>平权: 所有 slot 等重。LLM 每轮自主分配注意力。 |
| **Self-reflection**<br/>自省 | LLM sees current state → outputs action. No explicit reasoning trace fed back.<br/>LLM 看到当前状态 → 输出 action。无显式推理痕迹回馈。 | 4-step cognitive pipeline written by LLM every tick, re-read next tick.<br/>4 步认知管道每轮由 LLM 写, 下轮重读。 |
| **World model**<br/>世界模型 | Centralized state management. The engine "knows" what happened.<br/>中心化状态管理。引擎"知道"发生了什么。 | Distributed perception. Each agent sees a private sensory window. No agent sees the full state.<br/>分布式感知。每个 agent 只看到私有的感官窗口。无 agent 看到全态。 |
| **Experimental value**<br/>实验价值 | Tests whether the agent follows instructions correctly.<br/>测试 agent 是否按指令正确执行。 | Tests what emerges when no instructions are given at the semantic level.<br/>测试当语义层面零指令时能涌现出什么。 |

---

## Value · 价值

### As a research apparatus · 作为研究装置

The system answers a question that is difficult to ask in any existing framework:
**"What are the minimal architectural constraints necessary for social behavior to emerge between autonomous LLM-based agents?"**

这个系统回答一个在任何现有框架中都难以提出的问题:
**"基于 LLM 的自主代理之间涌现社会行为, 最小架构约束是什么？"**

By strictly separating atomic fact reporting (engine) from semantic interpretation (LLM),
the system creates a controlled environment where:

- Any observed social pattern can be traced back to a specific combination of engine-provided facts and LLM cognition
- The absence of a social pattern is equally informative — it means the current fact set is insufficient
- Each architectural component (cognitive pipeline, drive system, direction markers) can be independently ablated to measure its contribution

通过严格分离原子事实报告(引擎)和语义解释(LLM), 系统创造了一个受控环境:
- 任何观察到的社会模式都可以追溯到特定的引擎事实+LLM认知组合
- 社会模式的缺失同样具有信息量——意味着当前事实集合不足
- 每个架构组件(认知管道、驱动系统、方向标记)可以独立消融以测量其贡献

### As a design philosophy · 作为设计哲学

The project demonstrates that **refusing to encode domain knowledge into the engine**
is not a limitation — it is a generative constraint. The less the engine "understands,"
the more the LLM is forced to derive, and the more surprising the resulting behavior.

This is the inverse of standard software engineering — where we add features to increase capability.
Here, we subtract engine-level interpretation to increase emergent complexity.

项目证明**拒绝将领域知识编码进引擎**不是限制——而是生成性约束。
引擎"理解"得越少, LLM 被迫推导得越多, 产生的行为越出乎意料。
这与标准软件工程相反——标准做法是加功能以提高能力。这里是减引擎层解释以增加涌现复杂度。

---

## Potential Applications · 潜在应用

| Area · 领域 | Application · 应用 |
|---|---|
| **Multi-agent simulation**<br/>多代理模拟 | Economic systems, crowd behavior, organizational dynamics — with agents that derive their own strategies rather than executing pre-scripted behaviors.<br/>经济系统、人群行为、组织动态——代理自己推导策略而非执行预编脚本。 |
| **LLM evaluation**<br/>LLM 评估 | Measure an LLM's ability to detect social patterns, negotiate, and self-reflect under minimal environmental scaffolding.<br/>测量 LLM 在最小环境支架下检测社会模式、谈判、自省的能力。 |
| **Game design**<br/>游戏设计 | Autonomous NPCs whose social behavior is not scripted but genuinely responsive to accumulated interaction history.<br/>自主 NPC 的社交行为不是脚本固定而是真正响应累积的交互历史。 |
| **Cognitive architecture research**<br/>认知架构研究 | Test the effect of specific architectural components (self-reflection pipelines, drive models, attention mechanisms) on emergent agent behavior.<br/>测试特定架构组件(自省管道、驱动模型、注意力机制)对涌现 agent 行为的影响。 |
| **Social science modeling**<br/>社会科学建模 | Study how negotiation dynamics, trust formation, and cooperation emerge under controlled information constraints.<br/>研究在受控信息约束下谈判动态、信任形成与合作如何涌现。 |

---

## Quick Start · 快速开始

```bash
pip install -r requirements.txt
python main.py --validate-config             # Validate YAML configs · 验证配置
python main.py --runtime 180 \
    --world config/world_trade.yaml          # 12-NPC trade world · 12人交易世界
python -m pytest tests/ -q                   # 176 tests · 176 测试
```

---

## License · 许可证

MIT
