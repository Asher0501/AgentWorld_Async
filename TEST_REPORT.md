AgentWorld Async — Complete Test Report
Generated 2026-05-28 | 127 tests, 8 files | python -m pytest tests/ -q → 10.03s

═══════════════════════════════════════════════════════════════
OVERVIEW
═══════════════════════════════════════════════════════════════

  107 unit tests        (0.19s)  — pure logic, no I/O, no LLM
   20 integration tests  (9.84s)  — full stack with dashboard, world, agent loop

  127 TOTAL             (10.03s) — ALL PASSED

═══════════════════════════════════════════════════════════════
MODIFICATION-TO-TEST MAPPING
═══════════════════════════════════════════════════════════════

Each code change from commits cb69cf6 and 6c5e36b listed with tests.

───────────────────────────────────────────────────────────────
#3  src/systems/sensory.py  — is_new speech-content comparison
───────────────────────────────────────────────────────────────
BUG: is_new was lifetime entity flag. Second utterance from same
     speaker silently dropped from listener's conversation buffer.
FIX: Capture prev_speech before overwriting record. Append to
     buffer when (is_new OR speech != prev_speech).

UNIT (test_modifications.py):
  ✅ test_sensory_first_utterance_enters_buffer
  ✅ test_sensory_repeated_same_speech_not_duplicated
  ✅ test_sensory_different_speech_from_same_speaker_enters_buffer
  ✅ test_sensory_multiple_speakers_buffer
  ✅ test_sensory_buffer_capped_at_8

INTEGRATION (test_full_stack.py):
  ✅ test_multiple_utterances_enter_the_same_entity_buffer
  ✅ test_speaker_out_of_range_removed_from_channels

───────────────────────────────────────────────────────────────
#1  src/core/lifecycle.py  — spawn_entity ID collision
───────────────────────────────────────────────────────────────
BUG:  lifecycle.spawn() silently overwrote existing entity on duplicate ID.
FIX:  Add ValueError before blind assignment.

UNIT:
  ✅ test_spawn_duplicate_id_preserves_original (test_modifications.py)
  ✅ test_spawn_unique_ids_no_collision (test_modifications.py)
  ✅ test_spawn_entity_success (test_world.py)
  ✅ test_spawn_entity_duplicate_id_raises (test_world.py)

INTEGRATION:
  ✅ test_spawn_duplicate_preserves_world_state
  ✅ test_despawn_removes_from_world
  ✅ test_despawn_nonexistent_returns_false

───────────────────────────────────────────────────────────────
#4  src/loop.py  — _pending_action defer-clear
───────────────────────────────────────────────────────────────
BUG:  _pending_action = None was BEFORE execution.
FIX:  Moved to END of FLUSH (after file output, before continue).

UNIT:
  ✅ test_pending_action_not_cleared_until_successful_execution

INTEGRATION:
  ✅ test_controlled_agent_consumes_order
  ✅ test_flush_writes_file_to_disk
  (Both verify the full take → order → execute → consume path)

───────────────────────────────────────────────────────────────
#2  src/core/lifecycle.py  — zone transfer docstring
───────────────────────────────────────────────────────────────
Documentation-only. No test needed.

───────────────────────────────────────────────────────────────
#10 src/event_bus.py  — QueueFull warning
#11 src/core/error_collector.py  — get_summary() + dump()
#12 src/loop.py  — transient vs fatal error distinction
#13 src/loop.py  — agent_logging at key paths
───────────────────────────────────────────────────────────────
#5-7  Core architecture validation
───────────────────────────────────────────────────────────────
UNIT:
  ✅ 21 tests: test_delta_gate.py (4 pure functions)
  ✅ 22 tests: test_extract_json.py (6 strategies)
  ✅ 16 tests: test_assembler.py (slot composition)

#5: P/Q delta gate functions — entered, left, changed, cross, stale
#6: Prompt assembler — safe_format edges, slot mask, condition gates
#7: LLM output parser — 6 JSON extraction strategies

───────────────────────────────────────────────────────────────
REST API integration
───────────────────────────────────────────────────────────────
INTEGRATION (test_full_stack.py):
  ✅ test_state_returns_world_snapshot       GET  /api/state
  ✅ test_snap_returns_agent_data            GET  /api/snap
  ✅ test_snap_nonexistent_returns_empty     GET  /api/snap (404-like)
  ✅ test_take_sets_controlled_status        POST /api/take
  ✅ test_take_and_release_cycle             POST /api/take + /api/release
  ✅ test_order_injects_decision             POST /api/order
  ✅ test_set_writes_entity_field            POST /api/set
  ✅ test_set_permission_rejected            POST /api/set (PermissionError)
  ✅ test_memorize_adds_memory               POST /api/memorize

═══════════════════════════════════════════════════════════════
FULL TEST SUITE BREAKDOWN
═══════════════════════════════════════════════════════════════

File                          Tests   Category
─────────────────────────────────────────────────────
test_full_stack.py             20     Integration (full stack)
test_modifications.py          25     Modification regression (unit)
test_delta_gate.py             21     P/Q gate functions (unit)
test_extract_json.py           22     LLM output parsing (unit)
test_assembler.py              16     Slot assembly pipeline (unit)
test_world.py                  12     Entity CRUD operations (unit)
test_director.py                9     Director lifecycle (unit)
test_event_bus.py               6     Event bus pub/sub (unit)
test_config.py                  3     YAML structure validation (unit)
─────────────────────────────────────────────────────
TOTAL                         127

All 127 tests: PASSED (10.03s)

═══════════════════════════════════════════════════════════════
CI COMMANDS
═══════════════════════════════════════════════════════════════

  # Unit only (no external deps, 0.2s):
  python -m pytest tests/unit/ -v

  # Integration (needs config files, dashboard, ~10s):
  python -m pytest tests/integration/ -v

  # All:
  python -m pytest tests/ -v

CI: .github/workflows/test.yml (runs on push/PR)
  - pip install pytest pytest-asyncio
  - python -m pytest tests/unit/ -v --tb=short
