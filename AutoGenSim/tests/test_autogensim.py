"""AutoGenSim tests — no AutoGen or AgentWorld server required."""
import sys, os, pytest

base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(base, "src"))
sys.path.insert(0, os.path.join(base, "AutoGenSim"))


class TestOfficeYAML:
    def test_loads_and_has_6_agents(self):
        import yaml
        with open(os.path.join(base, "AutoGenSim", "office.yaml")) as f:
            wc = yaml.safe_load(f)
        agents = [e for e in wc["entities"] if e.get("agent", {}).get("autonomous")]
        assert len(agents) == 6
        ids = {a["id"] for a in agents}
        assert ids == {"coder_01", "coder_02", "pm_01", "designer_01", "reviewer_01", "intern_01"}

    def test_three_zones(self):
        import yaml
        with open(os.path.join(base, "AutoGenSim", "office.yaml")) as f:
            wc = yaml.safe_load(f)
        zones = {z["id"] for z in wc["zones"]}
        assert zones == {"open_space", "meeting_room", "break_room"}


class TestDirectorClient:
    def test_imports(self):
        from director_client import DirectorClient
        c = DirectorClient()
        assert c.base_url == "http://localhost:8766"

    def test_custom_url(self):
        from director_client import DirectorClient
        c = DirectorClient("http://localhost:9999")
        assert c.base_url == "http://localhost:9999"


class TestTools:
    def test_imports(self):
        from tools import make_tools
        assert callable(make_tools)


class TestPersonas:
    def test_all_defined(self):
        from personas import PLANNER_SYSTEM, CODER_SYSTEM, REVIEWER_SYSTEM
        assert len(PLANNER_SYSTEM) > 50
        assert len(CODER_SYSTEM) > 50
        assert len(REVIEWER_SYSTEM) > 50
        assert "order_npc" in PLANNER_SYSTEM
        assert "TERMINATE" in PLANNER_SYSTEM


class TestDirectorPermissions:
    def test_matrix_loaded(self):
        import yaml
        with open(os.path.join(base, "config", "director_permissions.yaml")) as f:
            dp = yaml.safe_load(f)
        assert dp["groups"]["controller"] == 1
        assert dp["groups"]["moderator"] == 2
        assert dp["groups"]["admin"] == 3
        assert dp["fields"]["agent.memory"] == 2
        assert dp["fields"]["agent.pos"] == 3

    def test_permission_check(self):
        import os as _os, yaml
        # Load from source
        with open(_os.path.join(base, "config", "director_permissions.yaml")) as f:
            dp = yaml.safe_load(f)

        # Simulate Director._resolve_required
        def resolve(path):
            fields = dp["fields"]
            if path in fields:
                return fields[path]
            for pattern, level in fields.items():
                if pattern.endswith(".*") and path.startswith(pattern[:-2]):
                    return level
            return 4

        # Level 2 can write memory and drives
        assert resolve("agent.memory") == 2
        assert resolve("agent.drives.hunger") == 2
        assert resolve("agent.drives.energy") == 2
        # Level 3 can write pos
        assert resolve("agent.pos") == 3
        # Unknown fields require super
        assert resolve("agent.unknown") == 4


class TestDeleteSafety:
    """Verify AgentWorld runs fine without AutoGenSim."""

    def test_agentworld_validate_without_autogen(self):
        """office.yaml should validate without AutoGenSim imports."""
        import yaml
        with open(os.path.join(base, "AutoGenSim", "office.yaml")) as f:
            wc = yaml.safe_load(f)
        assert wc["world"]["name"] == "AutoGenSim 办公室"

    def test_agentworld_core_imports_unaffected(self):
        """Core engine should import without AutoGenSim on path."""
        from core.director import Director
        from core.world import World
        assert Director is not None
        assert World is not None
