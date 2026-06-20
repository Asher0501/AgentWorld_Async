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

## Table of Contents · 目录

- [1. The Question · 问题](#1-the-question--问题)
  - [1.1 What Everyone Assumes · 所有人默认的前提](#11-what-everyone-assumes--所有人默认的前提)
  - [1.2 Where Meaning Lives · 意义归谁管](#12-where-meaning-lives--意义归谁管)
- [2. Design Philosophy · 设计哲学](#2-design-philosophy--设计哲学)
  - [2.1 Semantic Compression as Premature Abstraction · 语义压缩即过早抽象](#21-semantic-compression-as-premature-abstraction--语义压缩即过早抽象)
  - [2.2 Constraint as Generative Force · 约束即生成力](#22-constraint-as-generative-force--约束即生成力)
- [3. Architecture · 架构](#3-architecture--架构)
  - [3.1 The Ontological Boundary · 本体论边界](#31-the-ontological-boundary--本体论边界)
  - [3.2 The Physics Engine · 物理引擎](#32-the-physics-engine--物理引擎)
  - [3.3 The Meaning Engine · 意义引擎](#33-the-meaning-engine--意义引擎)
  - [3.4 The Contract · 契约](#34-the-contract--契约)
- [4. Core Mechanisms · 核心机制](#4-core-mechanisms--核心机制)
  - [4.1 Why Self-Reflection Matters · 自省的必要性](#41-why-self-reflection-matters--自省的必要性)
  - [4.2 Why Flat Priority Matters · 平权的必要性](#42-why-flat-priority-matters--平权的必要性)
  - [4.3 Why Information Asymmetry Matters · 信息不对称的必要性](#43-why-information-asymmetry-matters--信息不对称的必要性)
  - [4.4 Why Cognitive Heterogeneity Matters · 认知异质的必要性](#44-why-cognitive-heterogeneity-matters--认知异质的必要性)
- [5. Value & Comparison · 价值与对比](#5-value--comparison--价值与对比)
  - [5.1 The Narrator Problem · 叙述者问题](#51-the-narrator-problem--叙述者问题)
  - [5.2 Emergence vs. Simulation · 涌现 vs. 模拟](#52-emergence-vs-simulation--涌现-vs-模拟)
  - [5.3 Causal Traceability · 因果可追溯性](#53-causal-traceability--因果可追溯性)
  - [5.4 Concurrency as Structure · 并发作为结构](#54-concurrency-as-structure--并发作为结构)
  - [5.5 The Zero-Semantics Coordination Layer · 零语义协调层](#55-the-zero-semantics-coordination-layer--零语义协调层)
  - [5.6 What This Architecture Uniquely Enables · 这个架构唯一能做的事](#56-what-this-architecture-uniquely-enables--这个架构唯一能做的事)
- [6. The Epistemology of Emergence · 涌现的认识论](#6-the-epistemology-of-emergence--涌现的认识论)
- [7. Project Structure · 项目结构](#7-project-structure--项目结构)
- [8. Quick Start · 快速开始](#8-quick-start--快速开始)
- [9. Configuration System · 配置系统](#9-configuration-system--配置系统)
- [10. License · 许可证](#10-license--许可证)

---

## 1. The Question · 问题

### 1.1 What Everyone Assumes · 所有人默认的前提

Every AI system built today rests on an unexamined assumption: **the infrastructure should understand what it's doing.**

The database knows what a "user" is. The API knows what "authentication" means. The agent framework knows what "delegation" implies. This is not a bug — it's the foundation of software engineering. We encode domain knowledge into systems so they can serve domain purposes.

But this assumption creates a blind spot. It makes one question impossible to ask:

> **If the infrastructure understood nothing — not "cooperation," not "negotiation," not "trust" — could these behaviors still arise from autonomous agents interpreting raw facts?**

This is not a question about prompt engineering. It is not a question about better training data. It is a question about **the minimum architectural scaffolding required for social intelligence to emerge.**

当前所有 AI 系统都建立在一个未经审视的假设之上：**基础设施应该理解自己在做什么。** 数据库知道什么是"用户"，API 知道什么是"认证"，Agent 框架知道什么是"委派"。这不是缺陷——这是软件工程的基础。我们把领域知识编码进系统，让系统服务领域目的。

但这个假设创造了一个盲区。它让一个问题变得不可能提出：**如果基础设施什么都不理解——不理解"合作""谈判""信任"——这些行为还能从自主代理解读原始事实中涌现吗？** 这不是提示工程问题，不是训练数据问题，而是关于**社会智能涌现所需的最小架构支架**的问题。

### 1.2 Where Meaning Lives · 意义归谁管

All software systems make a choice about where meaning lives. Most distribute it: the database schema carries some, the application logic carries more, the UI carries the rest. The LLM is just another meaning-bearing component in the stack.

AgentWorld makes a different choice: **all meaning lives exclusively in the LLM.**

The engine — the entire non-LLM infrastructure — is semantically null. It tracks numbers, positions, and event counts. It never produces a label, a summary, or a judgment. It is a physics engine for facts, not a platform for actions.

This is the single architectural decision from which everything else follows.

所有软件系统都在"意义归谁管"这个问题上做了一个选择。大多数系统将意义分布在各层：数据库模式承载一部分，应用逻辑承载更多，UI 承载其余的。LLM 只是栈中又一个承载意义的组件。

AgentWorld 做了一个不同的选择：**所有意义只存在于 LLM 中。** 引擎——全部非 LLM 基础设施——在语义上为零。它追踪数字、位置和事件计数。它从不产生标签、摘要或判断。它是事实的物理引擎，不是行动的平台。

这是唯一的架构决策，其他一切都由此推演。

---

## 2. Design Philosophy · 设计哲学

### 2.1 Semantic Compression as Premature Abstraction · 语义压缩即过早抽象

Software engineers recognize premature optimization as a mistake: you optimize before you know where the bottleneck is, and you make the system harder to change.

Semantic compression is premature optimization in the dimension of **meaning**. When the engine produces "Agent A is pressuring Agent B," it has performed the following lossy transformation:

```
Atomic facts                         Compressed label
─────────────                        ────────────────
A spoke × target=B × 25 times
B never responded                   →  "A is pressuring B"
B's social_pressure = 100/100
```

The label destroys information. "Pressuring" could mean coercion, persuasion, or repeated inquiry. "Not responding" could mean ignoring, not hearing, or processing. By compressing three atomic facts into one label, the engine has **foreclosed alternative interpretations**.

This is the same pattern as premature abstraction in code: you replace concrete cases with a general category before you have enough examples to know what the right abstraction is. The difference is that here, the "code" is the LLM's reasoning, and the "abstraction" is the engine's summary.

**The axiom**: the engine must never compress facts into interpretations. It must report only what is measurable and atomic. Everything else is the LLM's job.

The entire codebase enforces exactly one invariant. Every other design decision is a corollary.

软件工程师知道过早优化是错误：你在不知道瓶颈在哪之前就优化，让系统更难变更。

语义压缩是意义维度的过早优化。当引擎产出"Agent A 在施压 Agent B"时，它完成了以下有损变换：原子事实被压缩成解释性标签，标签摧毁了信息。"施压"可以是胁迫、说服或反复询问。"不回应"可以是不理、没听到或在思考。将三个原子事实压缩为一个标签，引擎**阻塞了替代解释的可能性**。

这和代码中的过早抽象是同一个模式：在你有足够案例知道正确抽象是什么之前，用一般类别替代具体实例。区别在于，这里的"代码"是 LLM 的推理，"抽象"是引擎的摘要。

**公理**：引擎不得将事实压缩为解释。只能报告可度量的、原子的事实。其他一切都是 LLM 的工作。整个代码库强制唯一不变量。所有其他设计决策都是它的推论。

### 2.2 Constraint as Generative Force · 约束即生成力

Standard engineering is additive: to increase capability, you add features. This project demonstrates the inverse principle: **removing capability from the infrastructure increases complexity in the system.**

Each semantic constraint is a void that the LLM must fill. The engine doesn't know what a "conversation" is → the LLM must recognize conversational patterns from raw speech events. The engine doesn't know what "pressure" is → the LLM must derive social dynamics from event frequency and direction markers.

This is not just a different design choice. It's a different **theory of where complexity should live**. Additive design places complexity in the infrastructure (more code, more rules). Subtractive design forces complexity to emerge in the interpreter (more reasoning, more pattern recognition).

The engine's ignorance is not a limitation to be overcome. It is the experimental variable.

标准工程是加法式的：要提升能力，你加功能。本项目展示了反原则：**从基础设施中移除能力，会增加系统中的复杂度。**

每一个语义约束都是一个 LLM 必须填补的空白。引擎不知道什么是"对话"→ LLM 必须从原始语音事件中识别对话模式。引擎不知道什么是"压力"→ LLM 必须从事件频率和方向标记中推导社交动态。

这不只是不同的设计选择。这是对**复杂度应该存在于何处**的不同理论。加法式设计将复杂度置于基础设施（更多代码、更多规则）。减法式设计迫使复杂度在解释器中涌现（更多推理、更多模式识别）。

引擎的无知不是需要克服的限制。它是实验变量。

---

## 3. Architecture · 架构

### 3.1 The Ontological Boundary · 本体论边界

Most system architectures are organizational — they separate concerns for maintainability: data layer, business logic, presentation. The boundary is pragmatic.

AgentWorld's architecture is **ontological** — it separates two different kinds of existence:

| | Engine Layer · 引擎层 | Agent Layer · 代理层 |
|---|---|---|
| **Deals in** | Facts · 事实 | Meanings · 意义 |
| **Question** | What is? · 是什么？ | What does it mean? · 这意味着什么？ |
| **Operations** | Arithmetic, spatial math, event counting · 算术、空间计算、事件计数 | Interpretation, goal-setting, social reasoning · 解释、目标设定、社会推理 |

This is not MVC. In MVC, the controller knows what a "user action" is. Here, the engine has no concept of "action" — it only processes parameterized primitive calls. This is not client-server. In client-server, the server knows the semantics of its endpoints. Here, the engine routes calls by name but has no awareness of what any call accomplishes.

The boundary is **the core architectural decision**. Everything else — the cognitive pipeline, the drive system, the interface definitions — exists to make this boundary productive rather than restrictive.

大多数系统架构是组织性的——为了可维护性分离关注点：数据层、业务逻辑、呈现层。边界是务实的。

AgentWorld 的架构是**本体论的**——它分离两种不同的存在方式。引擎层处理事实（是什么？），代理层处理意义（这意味着什么？）。

这不是 MVC。MVC 中控制器知道什么是"用户操作"。这里引擎没有"操作"的概念——它只处理参数化的原语调用。这不是 client-server。client-server 中服务器知道其端点的语义。这里引擎按名称路由调用，但不知道任何调用完成的是什么。

这个边界是**核心架构决策**。其他一切——认知管道、驱动系统、接口定义——的存在都是为了让这个边界具有生产力而非限制性。

```
┌──────────────────────────────────────────────────────────────┐
│           AGENT LAYER — THE MEANING ENGINE · 意义引擎           │
│                                                               │
│  Cognitive Pipeline (4-step self-reflection, every tick)       │
│  认知管道 (4 步自省, 每轮强制)                                   │
│  ↓                                                            │
│  goal → perception → assessment → summary → action decision   │
│                                                               │
│  Receives: atomic facts from engine · 接收引擎的原子事实         │
│  Receives: own previous self-reflection · 接收自己的上轮反思      │
│  Outputs: action decision + interface calls · 输出行动决策+接口调用│
└────────────────────────┬─────────────────────────────────────┘
                         │ Two-slot dispatch · 双槽路由
┌────────────────────────▼─────────────────────────────────────┐
│         ENGINE LAYER — THE PHYSICS ENGINE · 物理引擎            │
│                                                               │
│  Spatial:    entity positions · zone grids · proximity         │
│  空间层:      实体位置 · 区域网格 · 邻近关系                      │
│  Drive:      numerical attribute decay (flat-priority)         │
│  驱动层:      数值属性衰减 (平权)                                 │
│  Sensory:    radius-based perception · speech routing          │
│  感官层:      半径感知 · 语音路由                                 │
│  Abstract:   graph edges (ownership · transfer)                │
│  抽象层:      图边 (所有权 · 转移)                                │
│                                                               │
│  Knows:      numbers · coordinates · timestamps · event counts │
│  知道:        数字 · 坐标 · 时间戳 · 事件计数                     │
│  Never:      interpretations · labels · behavioral summaries   │
│  绝不:        解释 · 标签 · 行为摘要                              │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 The Physics Engine · 物理引擎

The engine is what remains when you strip all semantics from a simulation framework. Four subsystems, each operating on pure quantities:

**Spatial** — grid-based world with zone partitioning. Entities have integer coordinates. Movement, proximity queries, zone transitions are all geometric operations. The engine knows *where* things are; it has no concept of *why* they're there or *what* being there means.

**Drive** — numerical attributes that change over simulation time according to configurable decay rates. All attributes are peer-equal: a social drive value of 85 is structurally identical to a hunger value of 85. The engine reports the number; it does not suggest action. Critically, the engine has no concept of "need" or "urgency" — those are LLM-inferred.

**Sensory** — radius-based information gathering. For each agent, the engine collects: which entities are within visual range (with distance and appearance), what speech was produced within hearing range (with direction markers mechanically injected based on recorded speech target). The direction marker is a pure string append: if `speech_target == observer_name`, append "to you." The engine has no concept of "conversation" or "addressing someone."

**Abstract** — a graph engine managing edges between entity nodes and item-type nodes. Seven primitives: spawn, despawn, relocate, holder transfer, attribute modify, node add, node remove. Edges store quantities (float). No edge carries semantic type information — the meaning of an edge is inferred from the node types at its endpoints.

引擎是当你从一个模拟框架中剥离所有语义后剩下的东西。四个子系统，每个操作纯量：

- **空间层**：坐标是整数，移动是几何操作。引擎知道事物*在哪*，没有概念它们*为什么*在那或*在那意味着什么*。
- **驱动层**：数值随时间衰减。所有属性平权——社交值 85 和饥饿值 85 在结构上完全相同。引擎报告数值，不暗示行动。引擎没有"需求"或"紧迫"的概念——这些是 LLM 推断的。
- **感官层**：半径信息采集。引擎机械地注入方向标记（语音目标 == 观察者名则追加"对你说"）。引擎没有"对话"或"对人说话"的概念。
- **抽象层**：图引擎管理边。边存储浮点数，不带语义类型信息——边的意义由端点节点类型推断。

### 3.3 The Meaning Engine · 意义引擎

Each agent is an independent LLM instance with:

- **Bounded perception** — sees only entities within sensory radius. This is not a narrative device; it's a structural constraint enforced by the engine's spatial query.
- **Persistent self-model** — the cognitive pipeline output from the previous tick, re-read before new sensory input. The agent confronts its own past reasoning before seeing the present.
- **Drive state** — numerical values that the agent can modify through interface calls. The agent decides the relationship between a number and its behavior.
- **Declarative interface** — YAML-defined tools for interacting with the world. The agent sees only the interface descriptions; it has no access to engine internals.

The agent loop runs as a four-phase pipeline: **Sense** (engine collects sensory data), **Gate** (change detection decides whether cognition is needed), **Decide** (LLM runs cognitive pipeline), **Enqueue** (action stored for delayed execution respecting action duration).

每个代理是独立的 LLM 实例，具有受限感知（引擎空间查询的结构性约束，不是叙事装置）、持久自我模型（上轮认知管道输出，在新感官数据之前被重读）、驱动状态（代理通过接口调用修改数值，代理自己决定数值和行为的关系）、声明式接口（YAML 定义的工具，代理只看到接口描述，无权访问引擎内部）。

代理循环四阶段：感知 → 门控 → 决策 → 排队。

### 3.4 The Contract · 契约

The interface between engine and agent is a formal contract defined entirely in YAML. Two key properties:

**Zero op-name branching** — the engine routes calls purely by interface name. There is no `if action == "trade"` in the engine code. The engine dispatches to a handler registered under a name; what that handler does is opaque to the engine.

**Domain agnostic** — interfaces are declared with parameter types and descriptions. The engine validates parameter shapes, not parameter semantics. The description string is for the LLM's consumption, not the engine's.

Physical interfaces (entity-level actions) map to Python handlers via YAML. Abstract interfaces (engine primitives) are gated by `expose_to_llm` — only explicitly exposed primitives appear in the agent's tool list. This means the engine can support primitives the LLM doesn't know about, and primitives the LLM sees are exactly those the experiment designer chose to expose.

引擎与代理之间的接口是完全由 YAML 定义的正式契约。

**零操作名分支**：引擎纯按接口名路由。引擎代码中没有任何 `if action == "xxx"`。引擎将调用派发给注册在某个名字下的处理器；处理器做什么对引擎是不透明的。

**领域无关**：接口声明参数类型和描述。引擎验证参数形态，不验证参数语义。描述字符串是给 LLM 看的，不是给引擎用的。

物理接口（实体级动作）通过 YAML 映射到 Python 处理器。抽象接口（引擎原语）通过 `expose_to_llm` 门控——LLM 看到的原语恰好是实验设计者选择暴露的。

---

## 4. Core Mechanisms · 核心机制

Each mechanism is not just a feature. Each is an answer to a specific experimental question. Together, their interactions produce the space in which emergence becomes possible.

每个机制不只是一个功能。每个机制是对一个特定实验问题的回答。它们的交互共同产生了涌现成为可能的空间。

### 4.1 Why Self-Reflection Matters · 自省的必要性

**The question**: Does an agent's ability to reflect on its own past reasoning change its social behavior?

Every tick, the agent must write four structured reflections — goal, perception, assessment, summary — before deciding an action. These are stored and become the first thing the agent reads on the *next* tick, before any new sensory input.

This ordering matters. The agent confronts its own previous mental state before seeing the current world state. This creates continuity of self-model across ticks — not as a prompt instruction ("remember who you are") but as an architectural constraint (your past reasoning is literally the first thing you see).

Without this pipeline, each tick is a fresh interpretation of current facts. The agent has no persistent "train of thought." With the pipeline, each decision is informed by the history of its own reasoning. The difference is measurable: agents with the pipeline develop multi-turn strategies; agents without it react.

**问题**：代理反思自身过去推理的能力是否改变其社交行为？

每轮，代理必须在决定行动前写四段结构化反思——目标、感知、评估、总结。这些被存储，并在*下一轮*成为代理在接收任何新感官输入之前首先阅读的内容。

这个顺序很重要。代理在看到当前世界状态之前，先面对自己的过往心理状态。这创造了跨轮次的自我模型连续性——不是通过提示指令（"记住你是谁"），而是通过架构约束（你过去的推理是你看到的第一段文字）。

没有管道：每轮是对当前事实的全新解释。代理没有持久的"思路"。有管道：每个决策都受自身推理历史的影响。差异是可度量的：有管道的代理发展出多轮策略；没有管道的代理只会反应。

### 4.2 Why Flat Priority Matters · 平权的必要性

**The question**: Does removing priority hierarchy from the drive system change how agents allocate attention?

In virtually every game and simulation, drives have priorities: survival > social > leisure. The system decides what matters most.

AgentWorld strips this away. All drive attributes are structurally identical — same decay mechanism, same value range, same interface for modification. There is no engine-level ordering of importance.

This means the LLM must perform **autonomous attention allocation** every tick. Given seven numbers (hunger=85, social=20, fun=15...), which deserves action? The engine provides no guidance. The agent must construct its own priority — and that construction becomes part of the observable behavior.

When two agents with identical drives make different choices, we learn something about how LLMs construct value. When the same agent makes different choices in different social contexts with identical drives, we learn something about social influence on cognition.

**问题**：从驱动系统中移除优先级层级是否改变代理分配注意力的方式？

在几乎所有游戏和模拟中，驱动有优先级：生存 > 社交 > 休闲。系统决定什么最重要。

AgentWorld 剥离了这一点。所有驱动属性结构相同——相同衰减机制、相同值域、相同修改接口。没有引擎级的"重要性"排序。LLM 必须每轮执行**自主注意力分配**。面对七个数字，哪个值得行动？引擎不提供任何指导。代理必须构建自己的优先级——这个构建过程成为可观察行为的一部分。

### 4.3 Why Information Asymmetry Matters · 信息不对称的必要性

**The question**: Is bounded, asymmetric information a necessary condition for social behavior?

If every agent knew everything, there would be no need for communication. Information asymmetry is what makes social interaction non-trivial.

Each agent perceives only what falls within its sensory radius. Two agents standing in different locations perceive different subsets of the world. No agent has access to another agent's internal state (drives, memory, reasoning). No agent can verify the completeness of its own information.

This is not a convenience — it's the **experimental substrate**. Every social behavior the system produces must operate on incomplete information. Trust, deception, inquiry, information-sharing — these are responses to not knowing. In a system with perfect information, none of them would arise.

**问题**：受限的、不对称的信息是社会行为的必要条件吗？

如果每个代理都知道一切，就不需要交流。信息不对称是让社交互动非平凡的原因。

每个代理只感知其感官半径内的东西。不同位置的代理感知到世界的不同子集。没有代理能访问其他代理的内部状态（驱动、记忆、推理）。没有代理能验证自身信息的完整性。

这不是便利——这是**实验基底**。系统产生的每个社会行为都必须在不完整信息上运作。信任、欺骗、询问、信息分享——这些都是对"不知道"的回应。在完美信息系统中，它们都不会产生。

### 4.4 Why Cognitive Heterogeneity Matters · 认知异质的必要性

**The question**: Does varying the cognitive architecture between agents affect emergent social patterns?

The prompt template delivered to each agent is assembled from configurable slots. Each slot can be individually enabled or disabled per agent. An agent might lack a "consistency check" slot (making it prone to self-contradiction) or have a "novelty seeking" trait (making it abandon repetitive situations).

This creates heterogeneous cognitive profiles from identical engine infrastructure. The same world, the same facts, but different agents process them through different cognitive lenses.

The experimental power is this: you can compare a homogeneous population (all agents share the same slot configuration) against a heterogeneous one, holding everything else constant. If social complexity differs, you've isolated the effect of cognitive diversity — a causal claim that would be impossible to make in any system where cognition and infrastructure are not cleanly separated.

**问题**：改变代理之间的认知架构是否影响涌现的社交模式？

每个代理的提示模板由可配置的槽位组装而成。每个槽位可单独启用或禁用。代理可能缺少"一致性检查"槽（容易自相矛盾）或具有"追求新奇"特质（容易放弃重复情境）。

这从相同的引擎基础设施中创造了异质的认知画像。相同的世界，相同的事实，但不同的代理通过不同的认知透镜处理它们。

实验能力在于：你可以比较同质群体（所有代理相同槽位配置）和异质群体，保持其他一切不变。如果社交复杂度不同，你就分离出了认知多样性的效应——这是一个在任何认知与基础设施不干净分离的系统中都无法做出的因果声明。

---

## 5. Value & Comparison · 价值与对比

表面上看，用本地数据库存放多个代理状态、用单个 LLM 轮流读取并生成各自行动，似乎可以替代本项目的架构。以下逐层分解为什么替代不了。

### 5.1 The Narrator Problem · 叙述者问题

**单一 LLM + 数据库的架构有一个不可消除的本质缺陷：LLM 本身就是信息桥梁。**

When one LLM simulates Agent A, then Agent B, its internal reasoning space is **shared**. You can prompt "you are now Agent B, you don't know what Agent A just decided," but you cannot prevent the LLM's weights and context from containing that information.

This is not a prompt engineering problem — it's an architectural one. Information asymmetry in a single LLM can only be a **narrative convention** ("pretend not to know"), never a **physical fact** (actually doesn't know).

AgentWorld's agents are independent LLM calls with strictly isolated context windows. Agent A's reasoning chain never appears in Agent B's context. Information asymmetry is **architecturally guaranteed**, not **prompt-requested**.

This means you can study the actual effect of information asymmetry on social behavior — not the effect of an LLM role-playing information asymmetry. These are different phenomena.

当一个 LLM 先生成 Agent A、再生成 Agent B 时，其内部推理空间是共享的。你可以提示"你现在是 Agent B，你不知道 Agent A 刚做了什么决定"，但无法阻止 LLM 的权重和上下文已经包含这些信息。这不是提示工程问题——是架构问题。信息不对称在单一 LLM 中只能是**叙事约定**（"假装不知道"），不能是**物理事实**（真正不知道）。

AgentWorld 的代理是独立 LLM 调用，上下文窗口严格隔离。信息不对称是**架构保证**，而非**提示请求**。这意味着你能研究信息不对称对社交行为的实际影响——而非研究 LLM 扮演信息不对称的效果。两者是不同现象。

### 5.2 Emergence vs. Simulation · 涌现 vs. 模拟

这是最深层的差异。

A single LLM can **simulate** emergence — it can generate a story about how a social pattern "appeared." The LLM knows what the pattern is; its reasoning contains teleology — the story has a direction.

AgentWorld **produces** emergence — no component knows what behavior will appear. The engine doesn't know (zero semantics). No individual agent knows (bounded perception). No global observer exists.

**Simulating emergence is retrospective — you know the destination and reconstruct the path. Producing emergence is prospective — the destination is unknown to every component of the system.**

This directly determines research value. Using a single LLM to simulate a multi-agent society measures the LLM's narrative capability. Running a multi-agent society on AgentWorld measures **what architectural conditions are sufficient for social behavior to arise** — a fundamentally different scientific question.

单一 LLM 可以**模拟**涌现——它可以生成一个关于某个社交模式"如何出现"的故事。LLM 知道这个模式是什么；它的推理包含目的论——故事有方向。

AgentWorld **产生**涌现——没有组件知道什么行为会出现。引擎不知道（零语义）。任何单个代理不知道（受限感知）。没有全局观察者存在。

**模拟涌现是追溯的——你知道终点，重构路径。产生涌现是前瞻的——终点对系统所有组件都是未知的。**

这直接决定研究价值。用单一 LLM 模拟多代理社会，测量的是 LLM 的叙事能力。用 AgentWorld 运行多代理社会，测量的是**什么架构条件足以催生社会行为**——一个根本不同的科学问题。

### 5.3 Causal Traceability · 因果可追溯性

单一 LLM 永远无法做到的事情：**消融研究**。

In AgentWorld, you can:
- **Remove the cognitive pipeline**: run the same initial conditions, compare behavior with/without 4-step self-reflection. A single LLM cannot "remove introspection" — its reasoning is holistic; you cannot surgically excise one part while keeping the rest identical.
- **Change perception radius**: shrink from 10 to 3, measure change in social complexity. A single LLM can do this narratively, but you're changing the LLM's *description* of limited perception, not the actual *information flow* — the LLM still "knows" the global state in its reasoning.
- **Remove direction markers**: strip "to you" vs. background speech labels, measure the agent's ability to distinguish directed communication. In a single LLM, this problem doesn't exist — the LLM inherently knows who is speaking to whom because it's generating all dialogue.

Each architectural component is independently toggleable. This makes causal inference possible: **observed behavior change can only come from the variable you changed.** This is the basic condition of experimental science. A single LLM cannot meet it because its "components" are products of LLM reasoning, not independently manipulable variables.

每个架构组件可独立开关。这让因果推断成为可能：**观察到的行为变化只可能来自你改变的变量。** 这是实验科学的基本条件。单一 LLM 不满足它，因为其"组件"是 LLM 推理的产物，不是可独立操作的变量。

### 5.4 Concurrency as Structure · 并发作为结构

单一 LLM 模拟多代理时，认知是**序列化**的。所有事件在一个推理链中线性展开。"同时发生"是叙事，不是事实。

AgentWorld 中代理是异步并发的。多个独立 LLM API 调用同时发出，在不同时间返回：

- **真实的竞态**：两个代理可能同时决定对同一实体执行互斥操作。不是模拟的冲突——是实际 API 时序导致的架构级非确定性。
- **不可预测的事件序**：不是"随机决定顺序"，而是网络延迟、LLM 推理耗时等物理因素决定谁先完成。
- **部分失效**：某个代理的 LLM 调用超时或报错，其他代理继续运行。单一 LLM 中，LLM 出错则整个"故事"中断。

### 5.5 The Zero-Semantics Coordination Layer · 零语义协调层

AutoGen、CrewAI、MetaGPT 等多代理框架的共同前提：**协调层知道代理在做什么。** 它们的协调器理解"任务委派""角色分配""对话轮次"。这是它们作为生产工具的优势。

但这也使它们不可能回答这个问题：**如果不告诉协调器"什么是合作"，代理之间会自发产生合作吗？** 框架已经替代理定义好了。你只能测试代理如何在给定语义框架内表现，无法测试语义框架本身是否必要。

AgentWorld 的引擎不定义任何社会概念。它只管理数量转移、位置变更、感官路由。让引擎不知道"合作"是什么——这正是研究"合作需要什么条件才会涌现"的前提。

This is the fundamental asymmetry between AgentWorld and every other multi-agent framework: they encode social semantics into coordination; AgentWorld studies what happens when coordination has no social semantics. Other frameworks skipped this question because they optimize for production, not for studying emergence.

### 5.6 What This Architecture Uniquely Enables · 这个架构唯一能做的事

| 能力 | 单一 LLM + DB | 典型 Agent 框架 | AgentWorld |
|---|---|---|---|
| 架构保证的信息不对称 | ✗ 叙事约定 | ✗ 协调器知道全部状态 | ✓ 上下文窗口物理隔离 |
| 因果消融研究 | ✗ 组件不可独立操作 | ✗ 组件耦合在框架语义中 | ✓ 每个组件可独立开关 |
| 真正的异步并发 | ✗ 序列化 | 部分 | ✓ 独立 API 调用，真实竞态 |
| 零语义协调层 | ✗ LLM 即协调器 | ✗ 协调器内嵌领域语义 | ✓ 引擎只管理数值和坐标 |
| 无观察者的涌现 | ✗ LLM 是隐含叙述者 | ✗ 协调器有全局视角 | ✓ 无组件拥有全局状态 |
| 测量架构条件对行为的影响 | ✗ LLM 推理即架构 | ✗ 框架语义即架构 | ✓ 架构与推理严格分离 |

AgentWorld Async 不是一个更好的故事生成器——它根本不是一个故事生成器。它是一个**社会涌现的实验装置**。它的价值不在于产出更有趣的叙事，而在于回答：**给自主代理最小的架构支架，它们能自行构建多复杂的社会？** 这个问题，单一 LLM 回答不了，其他框架没在问。

---

## 6. The Epistemology of Emergence · 涌现的认识论

If you claim a behavior "emerged," you must be able to answer: how do you know it wasn't programmed?

Three criteria distinguish genuine emergence from engineered behavior in this system:

**1. No component intended it.**
The engine has no semantic awareness — it cannot intend anything. No individual agent possesses the global information or long-term planning horizon to orchestrate a multi-agent pattern. If the pattern exists, it must be a byproduct of interaction, not the goal of any single component.

**2. It is not derivable from any single component's logic.**
A pattern is genuinely emergent only if you cannot deduce it by examining one agent's code, one YAML config, or one prompt template in isolation. You need the full interactive dynamic. The cognitive pipeline alone doesn't produce negotiation; the drive system alone doesn't produce cooperation; the sensory system alone doesn't produce trust. These behaviors arise only in the intersection.

**3. The system designer did not anticipate it.**
This is the hardest criterion and the most important one. The YAML configs, the prompt templates, the interface definitions — none of them encode or hint at the emergent pattern. If the designer can point to a config line and say "that's where I specified this behavior," it isn't emergence.

These criteria create a paradox: **to verify emergence, you must observe it. But the act of observation imposes narrative on what was, in the system itself, a sequence of raw events.** The trace logs contain no "plot." They contain timestamps, entity IDs, action texts, and drive values. Any pattern you perceive — any "story" — is your interpretation layered onto atomic facts.

This reflexivity is not a flaw. It's the same epistemological condition as any observational science. The system produces data. The researcher produces interpretation. The architecture's job is to ensure the data is clean enough that interpretation is constrained by fact, not by engine-level narrative.

如果你声称一个行为"涌现了"，你必须能回答：你怎么知道它不是被编程的？

三个标准区分真正的涌现与工程行为：

**1. 没有组件意图如此。** 引擎没有语义意识——它不能有意图。没有任何单个代理拥有编排多代理模式的全局信息或长期规划视野。如果模式存在，它必须是交互的副产物，不是任何单个组件的目标。

**2. 不能从任何单个组件的逻辑推导。** 一个模式只有当你无法通过孤立检查一个代理的代码、一个 YAML 配置或一个提示模板来推导它时，才是真正涌现的。你需要完整的交互动态。认知管道单独不产生谈判；驱动系统单独不产生合作；感官系统单独不产生信任。这些行为只在交互中出现。

**3. 系统设计者没有预期。** 这是最难也最重要的标准。YAML 配置、提示模板、接口定义——它们都不编码或暗示涌现模式。如果设计者可以指向某行配置说"这就是我指定这个行为的地方"，那就不是涌现。

这些标准创造了一个悖论：**要验证涌现，你必须观察它。但观察行为本身就在原始事件序列上叠加了叙事。** 追踪日志不包含"情节"。它们包含时间戳、实体 ID、行动文本和驱动值。你感知到的任何模式——任何"故事"——都是你叠加在原子事实上的解释。

这种自反性不是缺陷。它和任何观察性科学的认识论条件相同。系统产生数据。研究者产生解释。架构的职责是确保数据足够干净，让解释受事实约束而非受引擎级叙事约束。

---

## 7. Project Structure · 项目结构

```
06_AgentWorld_Async/
├── main.py                  # 单一入口 — 世界无关
├── requirements.txt         # Python 依赖
├── config/                  # 所有配置为 YAML（引擎无硬编码值）
│   ├── world.yaml           # 世界定义 (实体、区域、驱动)
│   ├── prompts.yaml         # 提示模板、槽位、输出模式
│   ├── abstract_primitives.yaml  # 引擎原语定义
│   ├── channels.yaml        # 通信通道配置
│   ├── layer_registry.yaml  # 实体层类型注册
│   ├── item_registry.yaml   # 物品类型定义
│   ├── slot_groups.yaml     # 注意力槽位组配置
│   ├── llm.yaml             # LLM 提供商配置
│   └── worlds/              # 世界特定的接口定义
├── src/
│   ├── core/                # 引擎基础设施（零语义状态机）
│   │   ├── world.py         # 世界模型、实体加载、生命周期
│   │   ├── graph.py         # 抽象图引擎 (7 个原语)
│   │   ├── mcp_engine.py    # 接口路由 (零操作名分支)
│   │   ├── clock.py         # 模拟时钟
│   │   ├── spatial_grid.py  # 空间分区
│   │   ├── lifecycle.py     # 实体生成/消灭管理
│   │   ├── alias_registry.py # O(1) 名称到 ID 解析
│   │   ├── director.py      # 外部代理控制接口
│   │   ├── session.py       # 会话管理
│   │   ├── delta_gate.py    # 门控变化检测
│   │   └── persistence.py   # 状态持久化
│   ├── agent/               # 代理认知系统
│   │   ├── brain.py         # LLM 决策接口
│   │   ├── drives.py        # 驱动属性模型
│   │   ├── memory.py        # 情节记忆缓冲
│   │   └── sensory_memory.py # 感官通道存储
│   ├── prompt/              # 提示装配
│   │   ├── assembler.py     # 模板 → 提示构建
│   │   └── loader.py        # YAML 提示加载
│   ├── systems/             # 引擎系统
│   │   ├── decay.py         # 驱动时间衰减
│   │   ├── interaction.py   # 代理间交互解析
│   │   └── sensory.py       # 感官数据采集
│   ├── layers/              # 实体层类型
│   ├── entity/              # 实体数据模型
│   ├── gateway/             # 外部通信网关
│   ├── channel.py           # 提示装配的通道抽象
│   ├── event_bus.py         # 内部事件路由
│   ├── loop.py              # 主代理循环 (阶段管道)
│   ├── worlds/              # 世界特定逻辑
│   ├── llm/                 # LLM 客户端抽象
│   ├── logger/              # 结构化日志
│   ├── telemetry/           # 可观测性
│   ├── cli/                 # CLI 命令实现
│   ├── frontend_shared/     # 共享前端数据结构
│   └── eval/                # 评估框架
├── tests/                   # 测试套件 (176 测试)
├── dashboard/               # Web 监控仪表盘
├── visual/                  # 可视化前端
├── studio/                  # Studio 工具
├── experiments/             # 实验配置
├── scripts/                 # 工具脚本
└── doc/                     # 架构文档
```

---

## 8. Quick Start · 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 验证配置文件
python main.py --validate-config

# 运行模拟
python main.py --runtime 180 --world config/world.yaml

# 带 Web 仪表盘运行
python main.py --dashboard 8766

# 带可视化前端运行
python main.py --visual 8767

# 运行测试套件
python -m pytest tests/ -q
```

**命令行选项：**

| 选项 | 说明 |
|---|---|
| `--runtime N` | 模拟时长 (秒) |
| `--world PATH` | 世界配置文件路径 |
| `--validate-config` | 仅验证 YAML 配置而不运行 |
| `--dashboard PORT` | 启动 Web 监控仪表盘 |
| `--visual PORT` | 启动像素可视化前端 |
| `--eval-report FILE` | 从 trace 生成评估报告 |
| `--output PATH` | 保存评估输出 |
| `--verbose [PATH]` | 启用详细引擎日志 |

---

## 9. Configuration System · 配置系统

所有系统行为通过 `config/` 目录下的 YAML 文件配置。引擎没有任何硬编码值——这是"零语义"原则在配置层的体现。改变代理行为、世界规则或实验条件不需要修改 Python 代码。

**核心配置文件：**

- `world.yaml` — 模拟世界：区域、实体及其层和特质、驱动属性及衰减率、时间尺度、验证约束
- `prompts.yaml` — 提示模板为可组合槽位、系统提示、输出 JSON 模式、文本标签
- `abstract_primitives.yaml` — 引擎原语，参数规约和 `expose_to_llm` 可见性门控
- `channels.yaml` — 引擎和提示装配之间的通信通道定义
- `layer_registry.yaml` — 实体层类型，Python 类映射和默认值
- `slot_groups.yaml` — 注意力槽位分组，实现异质代理认知画像
- `llm.yaml` — LLM 提供商配置（模型、端点、API 密钥）

---

## 10. License · 许可证

MIT
