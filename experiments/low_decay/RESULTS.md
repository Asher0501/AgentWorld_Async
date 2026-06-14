## 社交压力 drive — 实现与验证

### 改动（4 个文件，+32 行）

| 文件 | 改动 |
|---|---|
| `config/_sim_defaults.yaml` | `drive.attributes` 新增 `social_pressure: {min: 0, max: 100, decay: 0.0, description: "社交压力"}` |
| `config/world_trade.yaml` | 12 NPC `private_attrs` 加 `social_pressure: 0` |
| `experiments/low_decay/world_trade_low.yaml` | 同步 |
| `src/systems/interaction.py` | `interact()` 中检测定向对话 → target SP+8, agent SP−10 |

**零新字段、零新 slot、零新模块。**

### 行为

| 触发 | 引擎操作 |
|---|---|
| 别人对你说了话 | `social_pressure += 8`（引擎推断"有人找你了"） |
| 你对别人说了话 | `social_pressure −= 10`（你回应了——压力释放） |
| LLM 主动调 | `abs_attr_modify(entity=自己, attr=social_pressure, value=±N)` |

### 验证：180s 运行

```
托蜜ラ social_pressure:
  tick 15:  SP=0   打招呼                                    ← 初始
  tick 349: SP=8   报价并询问线索                              ← 杰洛特说话了
  tick 754: SP=16  再次询问术士线索                            ← 杰洛特又说话
  tick 819: SP=16  等待杰洛特回答                              ← 峰值
  
  她持续主动说话 → SP 被引擎释放 → 不会超过 16

杰洛特 social_pressure:
  tick 25:  SP=0   向托蜜拉打招呼
  tick 569: SP=8   询问稀有草药
  tick 735: SP=16  等待托蜜拉回答
```

### LLM 调用统计

- `abs_attr_modify` targeting `social_pressure`: 0 次
- 引擎自动 push/release 机制覆盖了所有场景，LLM 不需要显式管理

### 当前架构总结（整合后）

```
11 slot, 10 个注意力模块, 7 个 drive 属性（含 social_pressure）

┌─ 输入层 ─────────────────────────────────┐
│  LLM 每轮报告 input_attention (10模块)    │
│  → AgentLayer._input_attention           │
│  → 下一轮 priority_meta 动态权重          │
├─ 驱动层 ─────────────────────────────────┤
│  Engine decays: hunger, thirst, social,   │
│    energy, fun, mood                     │
│  Engine pushes: social_pressure (对话+8)   │
│  LLM modifies: abs_attr_modify (全部)     │
├─ 输出层 ─────────────────────────────────┤
│  11 orthogonal slots                     │
│  165 unit tests passing                  │
└──────────────────────────────────────────┘
```

### 待观察

- **特莉丝 SP 峰值 64**: 多个人同时对她说话导致。她是否响应了？
- **LLM 自主调 SP**: 目前 0 次——未来如果 LLM 学会"主动释放压力"，social_pressure 才真正成为 LLM 自己管理的认知变量
- **SP 阈值触发**: 目前 LLM 只是被动看到 SP 值，没有"SP > 50 → 必须回应"的约束。这是设计意图——LLM 自己判断，不教它做事
