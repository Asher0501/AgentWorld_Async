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

- [1. Project Overview · 项目概述](#1-project-overview--项目概述)
  - [1.1 What Problem Does This Solve? · 解决什么问题？](#11-what-problem-does-this-solve--解决什么问题)
  - [1.2 Core Principle · 核心原理](#12-core-principle--核心原理)
- [2. Design Philosophy · 设计哲学](#2-design-philosophy--设计哲学)
  - [2.1 The Axiom: No Semantic Compression · 公理：不进行语义压缩](#21-the-axiom-no-semantic-compression--公理不进行语义压缩)
  - [2.2 The Inversion: Subtract to Amplify · 反转：减法即放大](#22-the-inversion-subtract-to-amplify--反转减法即放大)
- [3. Architecture · 架构](#3-architecture--架构)
  - [3.1 Overview · 总览](#31-overview--总览)
  - [3.2 Layer 1: Engine · 引擎层](#32-layer-1-engine--引擎层)
  - [3.3 Layer 2: Agent · 代理层](#33-layer-2-agent--代理层)
  - [3.4 Layer 3: Interface System · 接口层](#34-layer-3-interface-system--接口层)
- [4. Core Mechanisms · 核心机制](#4-core-mechanisms--核心机制)
  - [4.1 Cognitive Pipeline · 认知管道](#41-cognitive-pipeline--认知管道)
  - [4.2 Drive System · 驱动系统](#42-drive-system--驱动系统)
  - [4.3 Distributed Perception · 分布式感知](#43-distributed-perception--分布式感知)
  - [4.4 Slot-Based Attention · 槽位注意力](#44-slot-based-attention--槽位注意力)
- [5. Value & Comparison · 价值与对比](#5-value--comparison--价值与对比)
  - [5.1 The Core Argument · 核心论点](#51-the-core-argument--核心论点)
  - [5.2 The Narrator Problem · 叙述者问题](#52-the-narrator-problem--叙述者问题)
  - [5.3 Emergence vs. Simulation · 涌现 vs. 模拟](#53-the-emergence-vs-simulation-distinction--涌现-vs-模拟的本质区别)
  - [5.4 Causal Traceability · 因果可追溯性](#54-causal-traceability--因果可追溯性)
  - [5.5 Concurrency as Structure · 并发作为结构属性](#55-concurrency-as-a-structural-property--并发作为结构属性)
  - [5.6 What Other Frameworks Cannot Do · 其它框架做不到什么](#56-what-other-agent-frameworks-cannot-do--其它框架做不到什么)
  - [5.7 Summary · 总结](#57-summary-what-this-architecture-uniquely-enables--总结这个架构唯一能做的事)
- [6. Emergent Properties · 涌现属性](#6-emergent-properties--涌现属性)
- [7. Project Structure · 项目结构](#7-project-structure--项目结构)
- [8. Quick Start · 快速开始](#8-quick-start--快速开始)
- [9. Configuration System · 配置系统](#9-configuration-system--配置系统)
- [10. License · 许可证](#10-license--许可证)

---

## 1. Project Overview · 项目概述

### 1.1 What Problem Does This Solve? · 解决什么问题？

All existing AI agent frameworks embed domain semantics into their engine layer. The developer writes behavioral rules, and the engine enforces them. Social dynamics — reciprocity, trust, negotiation — are programmed in advance.

这导致一个核心问题无法被研究：**如果引擎不提供任何语义引导，仅凭 LLM 自主解读原子事实，能自发涌现多少社会行为？**

AgentWorld Async 是一个受控实验装置，用于回答这个问题。它提供最小的事实集合（数值、坐标、原始感官数据），要求 LLM 在运行时推导所有语义。

### 1.2 Core Principle · 核心原理

```
Engine knows nothing → reports atomic facts → LLM interprets → behavior emerges
引擎一无所知 → 报告原子事实 → LLM 解释 → 行为涌现
```

引擎完全不知道代理在"做什么"。它只追踪数字、位置和事件计数。每个代理——独立的 LLM 实例——通过受限的感官窗口感知这些事实，必须自行构建对社交情境的理解。

---

## 2. Design Philosophy · 设计哲学

### 2.1 The Axiom: No Semantic Compression · 公理：不进行语义压缩

> **The engine must never produce interpretive labels. It must report only atomic, measurable facts.**
> **引擎不得产生解释性标签。只能报告原子的、可度量的事实。**

这是整个代码库强制执行的唯一不变量。所有其他设计决策都是它的推论。

如果引擎产出了类似"Agent A 在施压 Agent B"的文本，它就将多个原子事实压缩成了一个解释性标签。LLM 会推理这个*标签*而非*事实*——系统的实验价值在语义压缩发生的那一刻就被摧毁了。

引擎只能产出：
- 数值属性值
- 空间坐标
- 原始感官数据（看到谁、听到什么、时间戳）
- 事件计数

引擎**绝不**产出：
- 关系描述
- 行为解释
- 社交角色标签
- 情感状态

### 2.2 The Inversion: Subtract to Amplify · 反转：减法即放大

标准软件工程通过增加功能来提升能力。本项目展示了其反面：**移除引擎层的语义解释能增加涌现复杂度。**

引擎"理解"得越少，LLM 被迫推导得越多。引擎语义的每一次削减都是一个生成性约束——它迫使代理建立自己的解释框架，产生真正涌现而非预先编排的行为。

---

## 3. Architecture · 架构

### 3.1 Overview · 总览

```
┌──────────────────────────────────────────────────────────────┐
│                  AGENT LAYER (LLM — SOLE INTERPRETER)          │
│                  代理层 (LLM — 唯一解释者)                       │
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
│                  ENGINE LAYER (ZERO SEMANTICS)                 │
│                  引擎层 (零语义)                                  │
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
│  Outputs:    numbers · coordinates · timestamps · raw events   │
│  产出:        数字 · 坐标 · 时间戳 · 原始事件                     │
│  Never:      interpretations · labels · behavioral summaries   │
│  绝不:        解释 · 标签 · 行为摘要                              │
└──────────────────────────────────────────────────────────────┘
```

系统运行为两个干净分离的层，中间以 YAML 定义的接口连接。引擎处理状态转移；LLM 解释意义。两层互不具有对对方的语义感知。

### 3.2 Layer 1: Engine · 引擎层

引擎是一个**零语义状态机**。它不含任何领域词汇，不做任何解释性判断。

**空间子系统** — 管理实体在基于网格的世界中的位置，支持区域划分。处理移动、邻近查询和区域转移。所有坐标为原始整数；距离以网格单位度量。

**驱动子系统** — 维护随模拟时间衰减的数值属性。所有属性平权，无优先级体系。引擎报告数值；绝不暗示某个值"意味着"什么或代理"应该"怎么做。

**感官子系统** — 从每个代理的私有感官半径收集原始感知数据。报告哪些实体可见、说了什么话、语音来自哪个方向。引擎仅根据记录的对话目标机械注入方向标记，不做任何意图解释。

**抽象子系统** — 管理实体与物品类型之间所有权边的图引擎。支持七种原始操作（生成、消灭、重定位、持有转移、属性修改、节点增删）。图是纯数值的：边存储数量，不存储语义。

### 3.3 Layer 2: Agent · 代理层

每个代理是一个独立的 LLM 实例，具备：

- **受限感知**：仅看到感官半径内的实体
- **持久记忆**：近期事件的情节缓冲
- **驱动状态**：随时间衰减的数值属性
- **行动接口**：YAML 定义的与世界交互的工具

代理循环以阶段管道运行：

1. **Sense · 感知** — 引擎收集当前感官数据，更新驱动值
2. **Gate · 门控** — 变化检测判断新输入是否值得做出决策
3. **Decide · 决策** — LLM 运行认知管道，产出行动决策
4. **Enqueue · 排队** — 行动被存储以便延迟执行（尊重行动耗时）

### 3.4 Layer 3: Interface System · 接口层

接口系统通过 YAML 定义的规约将代理决策连接到引擎操作。具有两个关键属性：

- **零操作名分支**：引擎纯按接口名路由，不根据操作语义做条件判断
- **领域无关**：接口声明式定义；引擎不知道任何接口"做"什么

物理接口（实体级动作）由 YAML 定义并映射到 Python 处理器。抽象接口（引擎原语）同样由 YAML 定义，通过 `expose_to_llm` 门控——只有显式暴露的原语才会出现在 LLM 的工具列表中。

---

## 4. Core Mechanisms · 核心机制

### 4.1 Cognitive Pipeline · 认知管道

每轮，每个代理必须经过 4 步自省过程后方可决定行动。管道输出被存储，并在下一轮由同一个代理重读，形成持久的自省追踪。

| Step · 步骤 | Question · 问题 | Stored As · 存储为 |
|---|---|---|
| goal · 目标 | What am I trying to achieve? · 我要达成什么？ | 文本, 下轮重读 |
| perception · 感知 | What do I perceive right now? · 我此刻感知到什么？ | 文本, 下轮重读 |
| assessment · 评估 | How does perception affect my goal? · 感知如何影响目标？ | 文本, 下轮重读 |
| summary · 总结 | What has been happening recently? · 最近发生了什么？ | 文本, 下轮重读 |

认知管道排在所有新环境事实之前。LLM 必须先看到自己上一轮的反思，再看到新的感官输入。这强制了跨轮次的自我意识连续性。

### 4.2 Drive System · 驱动系统

驱动系统通过数值属性建模代理的内部状态。关键设计属性：

**平权** — 所有属性地位平等。不存在固定优先级决定代理应该关注哪个属性。LLM 每轮自主分配注意力。

**信号而非命令** — 高驱动值是事实，而非指令。LLM 感知数值并决定是否对其采取行动。驱动值与行为之间不存在引擎级的因果绑定。

**LLM 自写感受** — 除数值外，代理可写自由文本描述内部状态。该文本在下轮被重读，创造定性的连续性。

### 4.3 Distributed Perception · 分布式感知

没有代理能访问完整的世界状态。每个代理感知到的是：
- 在视觉半径内的实体
- 对它的定向对话以及听觉范围内的背景对话
- 自身的驱动值、持有物和记忆

这创造了根本性的分布式信息环境。不同代理有不同的观察，没有任何代理能验证另一个代理的完整状态。社交行为必须从代理推理不完整、不对称的信息中涌现——正如真实社交情境。

### 4.4 Slot-Based Attention · 槽位注意力

传递给每个代理的提示模板由可配置的槽位组合而成。每个槽位可按代理单独启用或禁用，创造异质的"认知画像"。

这支持实验控制：研究者可以比较不同提示配置下代理的行为差异，消融单个组件以测量其对涌现现象的贡献。

---

## 5. Value & Comparison · 价值与对比

### 5.1 The Core Argument · 核心论点

表面上看，用本地数据库存放多个代理状态、用单个 LLM 轮流读取并生成各自行动，似乎可以替代本项目的架构。这恰恰是对本项目价值最根本的误解。以下逐层分解为什么替代不了。

---

### 5.2 The Narrator Problem · 叙述者问题

**单一 LLM + 数据库的架构有一个不可消除的本质缺陷：LLM 本身就是信息桥梁。**

当一个 LLM 先生成 Agent A 的行动、再生成 Agent B 的行动时，它的内部推理空间是**共享**的。你可以提示"你现在是 Agent B，你不知道 Agent A 刚刚做了什么决定"，但你无法阻止 LLM 的权重和上下文已经包含了这些信息。

这不是提示工程问题——这是架构问题。信息不对称在单一 LLM 中只能是**叙事约定**（"假装不知道"），不能是**物理事实**（真正不知道）。

AgentWorld 的每个代理是独立的 LLM 调用，拥有严格隔离的上下文窗口。Agent A 的推理链永远不会出现在 Agent B 的上下文中。信息不对称是**架构保证**的，而非**提示请求**的。

这意味着什么？这意味着你能真正研究信息不对称对社会行为的影响——而非研究 LLM 扮演信息不对称的效果。两者测量到的是不同现象。

---

### 5.3 The Emergence vs. Simulation Distinction · 涌现 vs. 模拟的本质区别

这是最深层的差异。

单一 LLM 可以**模拟**涌现——它可以根据对世界的了解，生成一段关于"交易如何出现"的故事。LLM 本身知道交易是什么，它的推理包含了目的论——故事有一个方向。

AgentWorld **产生**涌现——没有任何组件知道什么行为会出现。引擎不知道（零语义），任何单个代理不知道（受限感知），不存在全局观察者。当一个复杂行为模式出现时，它是系统各部分交互的副产物，不是任何单一部分意图的结果。

**模拟涌现是追溯的——你已经知道终点，你在倒推路径。产生涌现是前瞻的——终点对系统所有组件都是未知的。**

这直接决定研究价值：用单一 LLM 模拟多代理社会，你测量的是 LLM 的叙事能力。用 AgentWorld 运行多代理社会，你测量的是**什么架构条件足以催生社会行为**——一个完全不同的科学问题。

---

### 5.4 Causal Traceability · 因果可追溯性

这是单一 LLM 永远无法做到的事情：**消融研究**。

在 AgentWorld 中，你可以做以下实验：

- **移除认知管道**：运行相同初始条件，比较有/无 4 步自省时的行为差异。单一 LLM 无法移除"自省"——因为 LLM 的推理是整体性的，你不能拆掉一个部分而保持其他不变。
- **改变感知半径**：将视觉半径从 10 缩到 3，测量社会模式复杂度变化。单一 LLM 也能做，但你是改变 LLM 对"感知范围"的*描述*，而非改变实际的*信息流*——LLM 仍然知道全局状态。
- **移除方向标记**：不给语音标注"对你说"vs 背景对话，测量代理区分定向/非定向交流的能力变化。单一 LLM 中不存在这个问题——LLM 天然知道谁在对谁说话，因为它在生成对话时就决定了。

每个架构组件都是可独立开关的。这让因果推断成为可能：**观察到的行为变化只可能来自你改变的变量。** 这是实验科学的基本条件。单一 LLM 和多代理框架都做不到，因为它们的"组件"是 LLM 推理的产物，不是可独立操作的变量。

---

### 5.5 Concurrency as a Structural Property · 并发作为结构属性

单一 LLM 模拟多代理时，认知是**序列化**的：Agent A 想、Agent A 做、Agent B 想、Agent B 做。所有事件在一个推理链中线性展开。即使你编造"同时发生"的叙事，LLM 实际上是依次处理的。

AgentWorld 中，代理是异步并发的。多个独立的 LLM API 调用同时发出，各自在不同时间返回。这意味着：

- **真正的竞态**：两个代理可能同时决定对同一个实体执行互斥操作。这不是模拟的冲突——是实际 API 时序导致的架构级非确定性。
- **不可预测的事件序**：不是"随机决定事件顺序"，而是网络延迟、LLM 推理耗时等真实物理因素决定了谁先完成。这对研究社会动态的时序敏感性至关重要。
- **部分失效**：某个代理的 LLM 调用可能超时或报错，而其他代理继续运行。单一 LLM 中，如果 LLM 出错，整个故事中断。

---

### 5.6 What Other Agent Frameworks Cannot Do · 其它框架做不到什么

AutoGen、CrewAI、MetaGPT 等多代理框架的共同前提是：**协调层知道代理在做什么。**

它们的协调器（orchestrator）理解"任务委派""角色分配""对话轮次"等概念。这是它们作为**生产工具**的优势——可以用来构建实际的 multi-agent 应用。

但这也使它们不可能回答以下问题：

> 如果不告诉协调器"什么是合作"，代理之间会自发产生合作吗？

因为框架已经替代理定义好了。你只能测试代理如何在给定语义框架内表现，无法测试语义框架本身是否是必要的。

**AgentWorld 的引擎不定义任何社会概念。** 它只管理数量转移、位置变更、感官路由。让引擎不知道"合作"是什么——这正是研究"合作需要什么条件才会涌现"的前提。其他框架跳过了这个问题，因为它们的目的是生产效率，不是研究涌现。

---

### 5.7 Summary: What This Architecture Uniquely Enables · 总结：这个架构唯一能做的事

| 能力 | 单一 LLM + DB | 典型 Agent 框架 | AgentWorld |
|---|---|---|---|
| 架构保证的信息不对称 | ✗ 只是叙事约定 | ✗ 协调器知道全部状态 | ✓ 上下文窗口物理隔离 |
| 因果消融研究 | ✗ 无法隔离组件 | ✗ 组件耦合在框架语义中 | ✓ 每个组件可独立开关 |
| 真正的异步并发 | ✗ 序列化 | 部分 | ✓ 独立 API 调用，真实竞态 |
| 零语义协调层 | ✗ LLM 即协调器 | ✗ 协调器内嵌领域语义 | ✓ 引擎只管理数值和坐标 |
| 无观察者的涌现 | ✗ LLM 是隐含叙述者 | ✗ 协调器有全局视角 | ✓ 无组件拥有全局状态 |
| 测量架构条件对行为的影响 | ✗ LLM 推理即架构 | ✗ 框架语义即架构 | ✓ 架构与推理严格分离 |

AgentWorld Async 不是一个更好的故事生成器——它根本不是一个故事生成器。它是一个**社会涌现的实验装置**。它的价值不在于产出更有趣的叙事，而在于回答：**给自主代理最小的架构支架，它们能自行构建多复杂的社会？** 这个问题，单一 LLM 回答不了，其他框架没在问。

---

## 6. Emergent Properties · 涌现属性

系统旨在产生真正涌现的行为——非预编、非硬编码、非引擎预期。当具有独立认知、受限感知和冲突内部状态的多个代理长期互动时，以下类别的涌现现象是可观测的：

- **策略收敛/发散** — 代理从相同认知架构中独立发展出相似或对立的互动策略
- **新颖接口组合** — 代理以接口设计者未预期的方式组合原始操作
- **互惠模式** — 无任何引擎级强制时产生的合作或竞争动态
- **信号-行为脱钩** — 代理感知高驱动值而不必然改变行为，展示对解释的自主权

这些不是代码实现的功能。它们是核心设计约束的后果：**给代理事实，而非意义。**

---

## 7. Project Structure · 项目结构

```
06_AgentWorld_Async/
├── main.py                  # 单一入口 — 世界无关
├── requirements.txt         # Python 依赖
├── config/                  # 所有配置为 YAML
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
│   ├── core/                # 引擎基础设施
│   │   ├── world.py         # 世界模型、实体加载、生命周期
│   │   ├── graph.py         # 抽象图引擎 (7 个原语)
│   │   ├── mcp_engine.py    # 接口路由 (零领域感知)
│   │   ├── clock.py         # 模拟时钟
│   │   ├── spatial_grid.py  # 空间分区
│   │   ├── lifecycle.py     # 实体生成/消灭管理
│   │   ├── alias_registry.py # O(1) 名称到 ID 解析
│   │   ├── director.py      # 外部代理控制接口
│   │   ├── session.py       # 会话管理
│   │   ├── delta_gate.py    # KL 门控的变化检测
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
│   ├── worlds/              # 世界特定逻辑 (接口、动作)
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

所有系统行为通过 `config/` 目录下的 YAML 文件配置。引擎没有任何硬编码值。

**核心配置文件：**

- `world.yaml` — 定义模拟世界：区域、实体及其层和特质、驱动属性及衰减率、时间尺度和验证约束
- `prompts.yaml` — 定义所有提示模板为可组合槽位、系统提示、输出 JSON 模式和文本标签
- `abstract_primitives.yaml` — 定义引擎原语，包含参数规约和 `expose_to_llm` 可见性门控
- `channels.yaml` — 定义引擎和提示装配之间的通信通道
- `layer_registry.yaml` — 定义实体层类型，包含 Python 类映射和默认值
- `slot_groups.yaml` — 定义注意力槽位分组，用于异质代理认知画像
- `llm.yaml` — LLM 提供商配置（模型、端点、API 密钥）

添加新的代理行为、世界配置或实验条件无需修改代码——仅需修改 YAML。

---

## 10. License · 许可证

MIT
