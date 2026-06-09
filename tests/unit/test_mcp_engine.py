"""Unit tests for MCPEngine."""
import pytest
from core.mcp_engine import MCPEngine, Layer, Interface, ParamDef, Result


class TestRegistration:
    def test_register_and_route(self):
        mcp = MCPEngine()
        called = []

        def echo(**kw):
            called.append(kw)

        layer = Layer(name="test", interfaces={
            "echo": Interface(name="echo", desc="Echo test", handler=echo,
                              params=[ParamDef(name="msg", type="str")])
        })
        mcp.register_layer("test", layer)
        r = mcp.route("test", {"interface": "echo", "params": {"msg": "hi"}})
        assert r.ok
        assert called[0]["msg"] == "hi"

    def test_nonexistent_layer(self):
        mcp = MCPEngine()
        r = mcp.route("ghost", {"interface": "x", "params": {}})
        assert not r.ok
        assert "ghost" in r.error

    def test_nonexistent_interface(self):
        mcp = MCPEngine()
        mcp.register_layer("test", Layer(name="test", interfaces={
            "a": Interface(name="a", handler=lambda **kw: None)
        }))
        r = mcp.route("test", {"interface": "b", "params": {}})
        assert not r.ok
        assert "不存在" in r.error or "does not exist" in r.error

    def test_missing_required_param(self):
        mcp = MCPEngine()
        mcp.register_layer("test", Layer(name="test", interfaces={
            "doit": Interface(name="doit", handler=lambda **kw: None,
                              params=[ParamDef(name="x", type="int")])
        }))
        r = mcp.route("test", {"interface": "doit", "params": {}})
        assert not r.ok
        assert "x" in r.error

    def test_route_all_batch(self):
        mcp = MCPEngine()
        log = []
        mcp.register_layer("a", Layer(name="a", interfaces={
            "op": Interface(name="op", handler=lambda **kw: log.append(("a", kw)))
        }))
        mcp.register_layer("b", Layer(name="b", interfaces={
            "op": Interface(name="op", handler=lambda **kw: log.append(("b", kw)))
        }))
        results = mcp.route_all({
            "a": [{"interface": "op", "params": {"qty": 3}}],
            "b": [{"interface": "op", "params": {"qty": 7}}],
        })
        assert results["a"][0].ok
        assert results["b"][0].ok
        assert log == [("a", {"qty": 3}), ("b", {"qty": 7})]


class TestToolList:
    def test_tool_list_includes_interfaces(self):
        mcp = MCPEngine()
        mcp.register_layer("test", Layer(name="test", interfaces={
            "eat": Interface(name="eat", desc="Eat food",
                             params=[ParamDef("entity", "alias")]),
        }))
        text = mcp.tool_list("test")
        assert "eat" in text
        assert "entity:alias" in text
        assert "Eat food" in text

    def test_tool_list_role_filter(self):
        mcp = MCPEngine()
        mcp.register_layer("test", Layer(name="test", interfaces={
            "a": Interface(name="a"), "b": Interface(name="b"),
        }))
        text = mcp.tool_list("test", role_keys={"a"})
        assert "a" in text
        assert "b" not in text

    def test_tool_list_empty_layer(self):
        mcp = MCPEngine()
        assert mcp.tool_list("ghost") == ""


class TestLayer:
    def test_subset(self):
        layer = Layer(name="x", interfaces={
            "a": Interface(name="a"), "b": Interface(name="b"),
        })
        sub = layer.subset({"a"})
        assert "a" in sub
        assert "b" not in sub
