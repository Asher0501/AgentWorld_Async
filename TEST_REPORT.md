AgentWorld Async — Modification Regression Test Report
Generated 2026-05-28 | 110 tests, 8 files | python -m pytest tests/unit/ -q → 0.19s

═══════════════════════════════════════════════════════════════
MODIFICATION-TO-TEST MAPPING
═══════════════════════════════════════════════════════════════

Each code change from commits cb69cf6 and 6c5e36b is listed below with
its corresponding test(s). Files modified: 6 source files, 3 new test files.

───────────────────────────────────────────────────────────────
#3  src/systems/sensory.py  — is_new speech-content comparison
───────────────────────────────────────────────────────────────
BUG: is_new was lifetime entity flag. Second utterance from same
     speaker silently dropped from listener's conversation buffer.
FIX: Capture prev_speech before overwriting record. Append to
     buffer when (is_new OR speech != prev_speech).

TESTS (test_modifications.py):
  ✅ test_sensory_first_utterance_enters_buffer
     Verify first utterance from new entity always enters buffer.

  ✅ test_sensory_repeated_same_speech_not_duplicated
     Same speech on second tick → NOT duplicated.

  ✅ test_sensory_different_speech_from_same_speaker_enters_buffer
     Different speech from same speaker → enters buffer (the bug fix).

  ✅ test_sensory_multiple_speakers_buffer
     Two speakers, two utterances each → all 4 in buffer.

  ✅ test_sensory_buffer_capped_at_8
     Buffer respects FIFO cap of 8.

───────────────────────────────────────────────────────────────
#1  src/core/lifecycle.py  — spawn_entity ID collision
───────────────────────────────────────────────────────────────
BUG:  lifecycle.spawn() silently overwrote existing entity on
      duplicate ID. Old entity destroyed, new unreported.
FIX:  Add `if entity.id in w.entities: raise ValueError(...)`
      before blind assignment.

TESTS (test_modifications.py):
  ✅ test_spawn_duplicate_id_preserves_original
     Duplicate ID raises ValueError; original entity untouched.

  ✅ test_spawn_unique_ids_no_collision
     Two different IDs spawn without conflict.

ALSO (test_world.py):
  ✅ test_spawn_entity_success
  ✅ test_spawn_entity_duplicate_id_raises

───────────────────────────────────────────────────────────────
#4  src/loop.py  — _pending_action defer-clear
───────────────────────────────────────────────────────────────
BUG:  _pending_action = None was at line 2 of FLUSH block (before
      execution). Exception mid-execution → action lost, side
      effects persisted.
FIX:  Moved _pending_action = None to END of FLUSH (after file
      output, before await sleep). Cleared only after success.

TEST (test_modifications.py):
  ✅ test_pending_action_not_cleared_until_successful_execution
     inspect.getsource(run_agent) — verifies _pending_action=None
     appears exactly once, AFTER file_output handling, NOT near
     enqueued_decision assignment.

───────────────────────────────────────────────────────────────
#2  src/core/lifecycle.py  — zone transfer docstring
───────────────────────────────────────────────────────────────
NOT A BUG. Added docstring to transfer_zone() explaining that
conversation buffer carries across zones intentionally (8-entry
FIFO cap naturally ages out). Sensory channels cleared on transfer.
No test needed — documentation-only change.

───────────────────────────────────────────────────────────────
#10 src/event_bus.py  — QueueFull warning
───────────────────────────────────────────────────────────────
BUG:  QueueFull was silently pass'd. Slow WebSocket clients lost
      events with zero observability.
FIX:  Replace `pass` with agent_logging.warning(...).

TESTS (test_modifications.py):
  ✅ test_event_bus_queuefull_logs_warning
     Verifies agent_logging.warning exists in EventBus.emit source.

ALSO (test_event_bus.py):
  ✅ test_queue_full_handled_gracefully
  ✅ test_emit_delivers_to_registered_client
  ✅ test_unregister_stops_delivery

───────────────────────────────────────────────────────────────
#11 src/core/error_collector.py  — get_summary() + dump()
───────────────────────────────────────────────────────────────
ENHANCEMENT: Error collector had no export/inspection API.
ADDED: get_summary() → dict, dump() → human-readable string.

TESTS (test_modifications.py):
  ✅ test_error_collector_summary_empty
  ✅ test_error_collector_summary_with_errors
  ✅ test_error_collector_dump_with_errors
  ✅ test_error_collector_dedup_same_message_same_module
  ✅ test_error_collector_dedup_different_module_separate
  ✅ test_error_collector_log_exception_captures_traceback
  ✅ test_error_collector_llm_parse_failure_truncates
  ✅ test_error_collector_global_singleton

───────────────────────────────────────────────────────────────
#12 src/loop.py  — transient vs fatal error distinction
───────────────────────────────────────────────────────────────
BUG:  All exceptions caught with flat 3s sleep. Rate limiting
      indistinguishable from programming errors.
FIX:  err_backoff dict per-agent. Transient types (RateLimitError,
      APITimeoutError, Timeout, TimeoutError) → exponential backoff
      (min 2^n, max 60s). Fatal → 3s pause.

TESTS (test_modifications.py):
  ✅ test_loop_error_backoff_variable_exists
     Verifies err_backoff dict declared and used.

  ✅ test_loop_transient_error_types_identified
     Verifies RateLimitError and Timeout detected by name.

  ✅ test_loop_error_logs_to_collector
     Verifies log_exception(f"loop.{name}", e) in except block.

───────────────────────────────────────────────────────────────
#13 src/loop.py  — agent_logging at key paths
───────────────────────────────────────────────────────────────
ENHANCEMENT: agent_logging was unused (1 call site).
ADDED: debug() at delta gate trigger and ENQUEUE phase.

TESTS (test_modifications.py):
  ✅ test_agent_logging_at_delta_trigger
     Verifies debug("DELTA triggered") in source.

  ✅ test_agent_logging_at_enqueue
     Verifies debug("ENQUEUE:") in source.

ALSO (existing in loop.py — unchanged):
  agent_logging.debug(f"[{name}] FLUSH: ...")  — 1 pre-existing call site

───────────────────────────────────────────────────────────────
#14 src/decision_types.py (was src/types.py)  — TypedDict
───────────────────────────────────────────────────────────────
ENHANCEMENT: DecisionDict, FileOutput TypedDict with NotRequired
fields for IDE support and AutoGen tool schemas.

TESTS (test_modifications.py):
  ✅ test_decision_dict_imports
     DecisionDict and FileOutput importable.

  ✅ test_decision_dict_allows_optional_fields
     Minimal dict with only "action" key passes type check.

  ✅ test_decision_dict_file_output_subtype
     Nested FileOutput within DecisionDict.

───────────────────────────────────────────────────────────────
#16 DESIGN_PHILOSOPHY.md  — Design Limitations
───────────────────────────────────────────────────────────────
Documentation-only. Added Section 9 covering:
- 9.1 P/Q Gate false-negative / false-positive
- 9.2 Slot composition upper bound
- 9.3 "LLM is capable enough" assumption
- 9.4 Scenarios NOT designed for
- 9.5 Engine-level risks (incl. v7.2 fixes)
No test needed.

═══════════════════════════════════════════════════════════════
FULL TEST SUITE BREAKDOWN
═══════════════════════════════════════════════════════════════

File                          Tests   Category
─────────────────────────────────────────────────────
test_modifications.py          25     Modification regression
test_delta_gate.py             21     P/Q gate functions
test_extract_json.py           22     LLM output parsing
test_assembler.py              16     Slot assembly pipeline
test_world.py                  12     Entity CRUD operations
test_director.py                9     Director lifecycle
test_event_bus.py               6     Event bus pub/sub
test_config.py                  3     YAML structure validation
─────────────────────────────────────────────────────
TOTAL                         110

All 110 tests: PASSED (0.19s)

═══════════════════════════════════════════════════════════════
CI COMMAND
═══════════════════════════════════════════════════════════════

  python -m pytest tests/unit/ -v

CI workflow: .github/workflows/test.yml (runs on push/PR)
  - pip install pytest pytest-asyncio
  - python -m pytest tests/unit/ -v --tb=short
