# AgentWorld Async — Engineering Improvement Roadmap

Based on deep professional review analysis. 
Excludes academic (empirical evaluation, baselines, seed control).
Rests on four implicit architectural contracts from DESIGN_PHILOSOPHY.md.

## Architecture Contracts (reality check)

| Contract | What it means | Violated by |
|----------|--------------|-------------|
| 世界即真理 | Engine maintains consistent world state | #1 spawn overwrite, #4 partial write |
| 感官忠实报告 | Engine doesn't filter what LLM sees | #3 is_new silences repeated utterances |
| 决策被忠实执行 | LLM decision → full execution or full failure | #4, #12 catch-all swallows failures |
| 门控可靠 | P/Q Gate saves tokens as claimed | #5, #6, #7 — zero verification |

---

## Phase 0: Foundation — Data consistency (repair the contracts)

### #3 — Fix sensory is_new (HIGHEST PRIORITY)
- **File**: `src/systems/sensory.py:69`
- **Bug**: `is_new` is lifetime-tagged per entity — second utterance from same speaker silently dropped from listener's conversation buffer
- **Why critical**: Directly violates "引擎不替 LLM 做判断". Engine is making an implicit importance judgment by withholding data. Exactly the line DESIGN_PHILOSOPHY.md draws.
- **Fix**: Compare `speech` content instead of entity-id first-seen flag. If speech changed, append to buffer regardless of whether entity was seen before.

### #1 — Fix spawn_entity ID conflict
- **File**: `src/core/lifecycle.py:11`
- **Bug**: `w.entities[entity.id] = entity` — blind assignment, no collision check. Old entity silently destroyed, new entity unreported to caller.
- **Fix**: Add `if entity.id in w.entities: raise ValueError(...)` before assignment.

### #4 — Fix _pending_action clear-before-execute
- **File**: `src/loop.py:209`
- **Bug**: `al._pending_action = None` before interaction executes. If `interact()` throws mid-way, world has partial side effects (dialogue written, deltas applied) but engine lost the decision record.
- **Fix**: Move `al._pending_action = None` to end of FLUSH block (after successful execution).

### #2 — Document zone transfer buffer carryover (NOT A BUG)
- **File**: `src/core/lifecycle.py:41`
- **Decision**: 8-entry cap naturally ages out. Carrying conversation across zones = human memory behavior. Not a fix — add comment documenting the design intent.

---

## Phase 1: Test infrastructure (验证机制)

### Structure
```
tests/
├── conftest.py              # sys.path + mock LLM + inline world fixtures
├── pytest.ini               # asyncio_mode=auto, markers, testpaths
├── unit/                    # Pure logic, no filesystem, no LLM
│   ├── test_delta_gate.py
│   ├── test_assembler.py
│   ├── test_extract_json.py
│   ├── test_world.py
│   ├── test_director.py
│   ├── test_event_bus.py
│   ├── test_concurrency.py
│   ├── test_clock.py
│   ├── test_spatial_grid.py
│   ├── test_lifecycle.py
│   └── test_config.py
├── integration/             # Requires runtime env, optional LLM
│   ├── test_director_api.py
│   ├── test_controlled_agent.py
│   └── test_npc_file_output.py
└── scripts/                 # Manual scripts needing API key
    └── run_director_live.py  # ex-test_director.py
```

### Key design rules
- **unit/** tests: NO filesystem reads, NO YAML, NO LLM. Construct objects via inline dicts. `extract_json` and `delta_gate` are already pure functions.
- **Assembler testing**: `PromptLoader.__new__()` + inline `loader.data = {...}` dict — no file I/O.
- **World construction**: Inline config dict + `config/slot_groups.yaml` (version-controlled code asset, not test data).
- **AutoGenSim/tests/**: Stays in its own directory (independent deletability). CI runs it as separate step with skip-if-not-installed.

### CI (.github/workflows/test.yml)
```yaml
jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - run: pip install pytest pytest-asyncio
      - run: python -m pytest tests/unit/ -v
  integration-no-llm:
    runs-on: ubuntu-latest
    steps:
      - run: python -m pytest tests/integration/ -v -k "not llm"
```

---

## Phase 2: Critical unit tests (证明核心主张)

### test_delta_gate.py — 4 pure functions
- `channel_delta`: entity entered/left/changed for each channel
- `state_delta`: drive thresholds crossed, coin delta
- `stale_check`: timeout-based trigger
- `total_delta`: composite across all channels
- All zero-dependency — just pass dicts in, assert strings out.

### test_assembler.py — safe_format + assemble
- `safe_format`: existing keys replaced, missing keys preserved literally, empty ctx, None values
- `assemble`: slot condition gates, slot_mask filtering, template ordering, empty template

### test_extract_json.py — 6 strategies
- ```json ... ``` block, bare ``` block, mixed prefix, nested braces (depth tracking), JSON array, direct parse fallback

### test_world.py — entity CRUD
- `spawn_entity`: normal spawn, duplicate ID raises error
- `despawn_entity`: exists → True, missing → False
- `get_nearby_ids`: radius-based query
- World constructed from inline dict (2 agents, 1 zone)

---

## Phase 3: Error handling & observability (提升工程成熟度)

### #10 — event_bus QueueFull warning
- `src/event_bus.py:39` — replace `pass` with `agent_logging.warning(...)`

### #11 — error_collector.get_summary()
- `src/core/error_collector.py` — add `get_summary() -> dict` and `dump() -> str`

### #12 — loop.py transient vs fatal error distinction
- `src/loop.py:402` — catch-all split: `RateLimitError`/`Timeout` → exponential backoff, others → `log_exception` + continue

### #13 — agent_logging usage
- Add `agent_logging.debug()` to: sensory update start, delta trigger, interaction start, FLUSH complete

---

## Phase 4: Documentation & types (降低协作门槛)

### #14 — TypedDict decision contracts
- `src/types.py`: `DecisionDict(TypedDict)` — action, target_name, dialogue, duration, expects_reply, file_output, main_thread_update, main_thread_reason
- Brain.decide() return typed, AutoGen tool functions get schema source

### #16 — Design Limitations section
- Add to DESIGN_PHILOSOPHY.md: P/Q gate false-negative scenarios (sensory range boundary), slot composition upper bound (cross-slot ctx key references), small-model assumption (what happens with weaker LLMs), scenarios this architecture is NOT designed for (embodied continuous control, real-time game AI)

### #15 — README tone (lowest priority)
- Keep "删除胜过添加" as design tagline, reduce repetition frequency
- Let evidence (tests + data) carry the weight

---

## Execution order & dependency chain

```
Phase 0 (#3 → #1 → #4)       ← 修复地基（引擎契约）
    │
Phase 1 (tests/ structure)   ← 建立验证机制
    │
Phase 2 (4 critical tests)   ← 证明核心主张
    │
Phase 3 (error/observability) ← 工程成熟度
    │
Phase 4 (docs/types)         ← 协作门槛
```

Phases 0-2 are sequential. Phases 3-4 can parallel.

**Total estimate**: ~6 hours across all phases.

---

*Generated 2026-05-28 from deep professional review analysis.*
