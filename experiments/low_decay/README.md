# 低衰减实验 (Low Decay Experiment)

## 假设

**当生存需求衰减率降低至 1/3 时，NPC 会将注意力从重复的"吃/喝/社交"循环转移到人格定义的主线目标上。**
表现为面向目标的动作比率上升、动作多样性增加。

可证伪：如果衰减降低后面向目标的动作比率在统计上不显著增加，假设不成立。

## 对照设计

| 变量 | 对照组 (baseline) | 实验组 (low_decay) |
|---|---|---|
| thirst decay | 0.022 | 0.007 |
| hunger decay | 0.018 | 0.006 |
| social decay | 0.015 | 0.005 |
| energy decay | -0.01 | -0.003 |
| fun decay | 0.015 | 0.005 |
| mood decay | 0.0 | 0.0 |

## 测量指标

| 指标 | 定义 | 预期方向 |
|---|---|---|
| 生存动作比率 | `eat + take_out(food)` / total_actions | ↓ |
| 主线动作比率 | 动作文本匹配目标关键词 / total_actions | ↑ |
| 动作多样性 | unique_actions / total_actions | ↑ |
| 跨 zone 移动次数 | gate 穿越次数 | ↑ |
| 纯 commerce 交易占比 | 含 item 转移的 hand_over / total_actions | ↑ (主线多为 commerce) |

## 运行命令

```bash
cd /home/asher/Documents/01_Projects/06_AgentWorld_Async

# 对照组 x3 (默认 high decay)
python main.py --runtime 180 --persist experiments/low_decay/baseline_run1_$(date +%s).sqlite3
python main.py --runtime 180 --persist experiments/low_decay/baseline_run2_$(date +%s).sqlite3
python main.py --runtime 180 --persist experiments/low_decay/baseline_run3_$(date +%s).sqlite3

# 实验组 x3
python main.py --runtime 180 --world experiments/low_decay/world_trade_low.yaml --persist experiments/low_decay/lowdecay_run1_$(date +%s).sqlite3
python main.py --runtime 180 --world experiments/low_decay/world_trade_low.yaml --persist experiments/low_decay/lowdecay_run2_$(date +%s).sqlite3
python main.py --runtime 180 --world experiments/low_decay/world_trade_low.yaml --persist experiments/low_decay/lowdecay_run3_$(date +%s).sqlite3
```

## 分析

```bash
# Run after all 6 sims complete
python scripts/analyze_experiment.py experiments/low_decay/
```
