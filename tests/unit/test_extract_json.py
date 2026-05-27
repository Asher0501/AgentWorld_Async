"""Unit tests for extract_json — 6 strategies for LLM output parsing."""
import json
import pytest
from agent.brain import extract_json, _parse_llm_json


# ── Strategy 1: ```json ... ``` ──

def test_extract_json_code_block():
    raw = '```json\n{"action": "walk", "target": "door"}\n```'
    assert extract_json(raw) == '{"action": "walk", "target": "door"}'


def test_extract_json_code_block_no_lang():
    raw = '```\n{"action": "talk"}\n```'
    assert extract_json(raw) == '{"action": "talk"}'


def test_extract_json_code_block_with_prefix_text():
    raw = 'Here is my decision:\n```json\n{"action": "eat"}\n```'
    assert extract_json(raw) == '{"action": "eat"}'


# ── Strategy 2: bare { } with depth tracking ──

def test_extract_json_bare_braces():
    raw = 'leading text {"action": "idle", "target": "none"} trailing text'
    result = extract_json(raw)
    parsed = json.loads(result)
    assert parsed["action"] == "idle"


def test_extract_json_nested_braces():
    raw = '{"action": "talk", "meta": {"tone": "friendly"}}'
    result = extract_json(raw)
    parsed = json.loads(result)
    assert parsed["meta"]["tone"] == "friendly"


def test_extract_json_only_first_brace_pair():
    raw = '{"first": 1} and {"second": 2}'
    result = extract_json(raw)
    assert "first" in result
    assert "second" not in result


# ── Strategy 3: bare [ ] for arrays ──

def test_extract_json_array():
    """Strategy 2 (brace matching) runs before Strategy 3 (bracket matching),
    so arrays with objects inside extract the first object, not the full array."""
    raw = '[{"action": "walk"}, {"action": "talk"}]'
    result = extract_json(raw)
    parsed = json.loads(result)
    assert "action" in parsed  # extracts first object


def test_extract_json_nested_array_brackets():
    raw = '[[1, 2], [3, 4]]'
    result = extract_json(raw)
    parsed = json.loads(result)
    assert parsed == [[1, 2], [3, 4]]


# ── Strategy 4: pre-code-block text (standard markdown) ──

def test_extract_json_markdown_block_with_text():
    raw = 'Sure, here you go:\n\n```json\n{"key": "value"}\n```'
    assert "key" in extract_json(raw)


# ── Strategy 5: fallback — return raw ──

def test_extract_json_no_json_returns_raw():
    raw = "Just a plain text response, no JSON here at all."
    assert extract_json(raw) == raw


# ── Strategy 6: direct parseable JSON ──

def test_extract_json_already_clean_json():
    raw = '{"action": "eat"}'
    assert extract_json(raw) == '{"action": "eat"}'


# ── Edge cases ──

def test_extract_json_empty_string():
    assert extract_json("") == ""


def test_extract_json_whitespace_only():
    assert extract_json("   \n  ") == ""


def test_extract_json_broken_markdown_blocks():
    raw = '```\n{"a":1}\n'  # unclosed code block
    result = extract_json(raw)
    assert json.loads(result)["a"] == 1


# ── _parse_llm_json ──

def test_parse_llm_json_valid():
    result = _parse_llm_json('{"action": "walk"}', "test")
    assert result["action"] == "walk"


def test_parse_llm_json_invalid_returns_error_dict():
    result = _parse_llm_json("not json at all {{{", "test.source")
    assert result["parse_error"] is True
    assert result["source"] == "test.source"
    assert "raw_preview" in result


def test_parse_llm_json_with_code_block():
    raw = '```json\n{"status": "ok"}\n```'
    result = _parse_llm_json(raw, "test")
    assert result["status"] == "ok"


def test_parse_llm_json_extracts_from_noisy_prefix():
    raw = 'Some explanation text\n{"action": "greet", "dialogue": "hi"}'
    result = _parse_llm_json(raw, "test")
    assert result["action"] == "greet"
