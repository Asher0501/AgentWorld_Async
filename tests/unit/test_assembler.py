"""Unit tests for prompt assembly — safe_format + PromptAssembler. No filesystem."""
import pytest
from prompt.assembler import safe_format, PromptAssembler


# ── safe_format ──

def test_safe_format_simple():
    assert safe_format("Hello {name}", {"name": "World"}) == "Hello World"


def test_safe_format_missing_key_preserved():
    assert safe_format("Hello {name}", {}) == "Hello {name}"


def test_safe_format_multiple_keys():
    tpl = "{greeting} {name}"
    ctx = {"greeting": "Hi", "name": "Alice"}
    assert safe_format(tpl, ctx) == "Hi Alice"


def test_safe_format_mixed_missing_and_present():
    tpl = "{a} {b} {c}"
    ctx = {"a": "1", "c": "3"}
    assert safe_format(tpl, ctx) == "1 {b} 3"


def test_safe_format_empty_ctx():
    assert safe_format("{x}", {}) == "{x}"


def test_safe_format_no_braces():
    assert safe_format("plain text", {}) == "plain text"


def test_safe_format_format_spec_handling():
    tpl = "value: {num:.2f}"
    ctx = {"num": 3.14159}
    assert safe_format(tpl, ctx) == "value: 3.14"


def test_safe_format_none_value():
    tpl = "value: {x}"
    ctx = {"x": None}
    assert safe_format(tpl, ctx) == "value: None"


# ── PromptAssembler ──

class MockLoader:
    """Pretend PromptLoader without filesystem."""
    def __init__(self, data):
        self.data = data

    def get_template(self, name):
        return self.data.get("templates", {}).get(name, {})

    def get_system_prompt(self, name):
        return self.data.get("system_prompts", {}).get(name, "")

    def get_output_schema(self, name):
        return self.data.get("output_schemas", {}).get(name, {})


@pytest.fixture
def assembler():
    data = {
        "slots": {
            "persona": {"condition": "name", "template": "You are {name}"},
            "memory": {"condition": "memory_text", "template": "Recent: {memory_text}"},
            "unconditional": {"condition": "", "template": "Always present"},
            "drive_values": {"condition": "drives_table", "template": "Drives:\n{drives_table}"},
        },
        "templates": {
            "npc": {"slots": ["persona", "memory", "unconditional", "drive_values"]},
            "bare": {"slots": []},
        },
        "system_prompts": {
            "default": "Be a helpful agent.",
        },
        "output_schemas": {
            "v1": {"type": "json_object"},
        },
    }
    return PromptAssembler(MockLoader(data))


def test_assemble_all_slots_active(assembler):
    ctx = {"name": "Alice", "memory_text": "walked to bar", "drives_table": "hunger: 50"}
    result = assembler.assemble("npc", ctx)
    assert "You are Alice" in result
    assert "Recent: walked to bar" in result
    assert "Always present" in result
    assert "Drives:" in result


def test_assemble_condition_skips_missing_ctx(assembler):
    ctx = {"name": "Alice"}  # no memory_text → memory slot skipped
    result = assembler.assemble("npc", ctx)
    assert "You are Alice" in result
    assert "Recent:" not in result
    assert "Always present" in result


def test_assemble_empty_template(assembler):
    result = assembler.assemble("bare", {})
    assert result == ""


def test_assemble_slot_mask_filters(assembler):
    ctx = {"name": "Alice", "memory_text": "something"}
    result = assembler.assemble("npc", ctx, slot_mask={"persona": 1, "memory": 0, "unconditional": 1, "drive_values": 1})
    assert "You are Alice" in result
    assert "Recent:" not in result  # masked out
    assert "Always present" in result


def test_assemble_slot_order_preserved(assembler):
    ctx = {"name": "Alice", "memory_text": "x", "drives_table": "hunger:50"}
    result = assembler.assemble("npc", ctx)
    lines = result.split("\n\n")
    assert "You are Alice" in lines[0]
    assert "Recent:" in lines[1]
    assert "Always present" in lines[2]


def test_get_system_prompt(assembler):
    template_name = "npc"
    tpl_ref = assembler.loader.data["templates"][template_name]
    tpl_ref["system_prompt_ref"] = "default"
    assert "Be a helpful agent" in assembler.get_system_prompt(template_name)


def test_get_output_schema(assembler):
    template_name = "npc"
    tpl_ref = assembler.loader.data["templates"][template_name]
    tpl_ref["output_schema"] = "v1"
    schema = assembler.get_output_schema(template_name)
    assert schema["type"] == "json_object"


def test_get_temperature(assembler):
    template_name = "npc"
    tpl_ref = assembler.loader.data["templates"][template_name]
    tpl_ref["temperature"] = 0.5
    assert assembler.get_temperature(template_name) == 0.5
