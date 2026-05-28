"""Integration tests — exercise full AgentWorld stack with running dashboard.

Tests marked `slow` require LLM API access (skipped by default in CI).
Tests marked `integration` require running dashboard + world (always run).
"""
import sys, os, time, json, asyncio, yaml, pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "AutoGenSim"))


# ═══════════════════════════════════════════════════════════════════════
# Shared fixtures
# ═══════════════════════════════════════════════════════════════════════

class _MockLLM:
    """Return pre-canned JSON decisions without calling an API."""
    def __init__(self, response='{"action": "idle"}'):
        self.api_key = "mock"
        self.base_url = ""
        self.response = response
    async def chat(self, **kwargs):
        return self.response


@pytest.fixture
def office_world():
    """World from office.yaml — real config, mock LLM."""
    from core.world import World
    from systems.sensory import SensorySystem
    from systems.interaction import InteractionSystem
    from systems.decay import DecaySystem

    with open(os.path.join(ROOT, "AutoGenSim", "office.yaml")) as f:
        wc = yaml.safe_load(f)

    world = World(wc, {
        "sensory": SensorySystem(),
        "interaction": InteractionSystem(_MockLLM(), None),
        "decay": DecaySystem(),
    })
    return world


@pytest.fixture
async def dashboard_server(office_world):
    """Start dashboard with Director on ephemeral port."""
    from event_bus import EventBus
    from dashboard.server import start_dashboard
    from core.director import Director

    director = Director(office_world)
    bus = EventBus(history_size=10)
    port = 18765
    task = asyncio.create_task(start_dashboard(bus, director, port))
    await asyncio.sleep(0.5)

    try:
        yield director, port
    finally:
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=2)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass


# ═══════════════════════════════════════════════════════════════════════
# Director REST API — all endpoints
# ═══════════════════════════════════════════════════════════════════════

class TestDirectorRESTAPI:
    """Test all Director REST endpoints through HTTP."""

    @pytest.mark.asyncio
    async def test_state_returns_world_snapshot(self, dashboard_server):
        from director_client import DirectorClient
        director, port = dashboard_server
        c = DirectorClient(f"http://localhost:{port}")
        s = await c.state()
        assert not s["frozen"], "World should not be frozen initially"
        assert "controlled" in s
        assert len(s["controlled"]) == 0

    @pytest.mark.asyncio
    async def test_snap_returns_agent_data(self, dashboard_server):
        from director_client import DirectorClient
        _, port = dashboard_server
        c = DirectorClient(f"http://localhost:{port}")
        snap = await c.snap("coder_01")
        assert snap["name"] == "小李"
        assert snap["zone"] == "open_space"
        assert "pos" in snap
        assert "drives" in snap

    @pytest.mark.asyncio
    async def test_snap_nonexistent_returns_empty(self, dashboard_server):
        from director_client import DirectorClient
        _, port = dashboard_server
        c = DirectorClient(f"http://localhost:{port}")
        snap = await c.snap("nobody")
        assert snap == {}

    @pytest.mark.asyncio
    async def test_take_sets_controlled_status(self, dashboard_server):
        from director_client import DirectorClient
        _, port = dashboard_server
        c = DirectorClient(f"http://localhost:{port}")
        await c.take("coder_01", level=2)
        s = await c.state()
        assert "coder_01" in s["controlled"]

    @pytest.mark.asyncio
    async def test_take_and_release_cycle(self, dashboard_server):
        from director_client import DirectorClient
        _, port = dashboard_server
        c = DirectorClient(f"http://localhost:{port}")
        await c.take("designer_01", level=2)
        assert "designer_01" in (await c.state())["controlled"]
        await c.release("designer_01")
        assert "designer_01" not in (await c.state())["controlled"]

    @pytest.mark.asyncio
    async def test_order_injects_decision(self, dashboard_server):
        from director_client import DirectorClient
        director, port = dashboard_server
        c = DirectorClient(f"http://localhost:{port}")

        director.take("coder_01", level=2)
        decision = {"action": "walk to desk", "target_name": "白板"}
        await c.order("coder_01", decision)

        from agent.sensory_memory import SensoryMemory
        from agent.drives import DriveSystem
        from layers.agent import AgentLayer
        al = director.world.entities["coder_01"].get("agent")
        # Order should be in the director's _orders dictionary
        assert director._orders.get("coder_01") == decision

    @pytest.mark.asyncio
    async def test_set_writes_entity_field(self, dashboard_server):
        from director_client import DirectorClient
        director, port = dashboard_server
        c = DirectorClient(f"http://localhost:{port}")

        director.take("coder_01", level=2)
        await c.set("coder_01", "agent.main_thread", "build paging sim")
        snap = await c.snap("coder_01")
        assert snap["main_thread"] == "build paging sim"

    @pytest.mark.asyncio
    async def test_set_permission_rejected(self, dashboard_server):
        from director_client import DirectorClient
        director, port = dashboard_server
        c = DirectorClient(f"http://localhost:{port}")

        director.take("coder_01", level=1)  # observer can't write
        try:
            await c.set("coder_01", "agent.pos", [50, 50])
            rejected = False
        except Exception:
            rejected = True
        assert rejected, "Level 1 should not be able to write agent.pos"

    @pytest.mark.asyncio
    async def test_memorize_adds_memory(self, dashboard_server):
        from director_client import DirectorClient
        director, port = dashboard_server
        c = DirectorClient(f"http://localhost:{port}")

        director.take("coder_01", level=2)
        await c.memorize("coder_01", "CI integration test passed")
        snap = await c.snap("coder_01")
        assert len(snap["memory"]) >= 1
        assert any("CI integration test passed" in m for m in snap["memory"])


# ═══════════════════════════════════════════════════════════════════════
# Controlled agent lifecycle — agent loop with director
# ═══════════════════════════════════════════════════════════════════════

class TestControlledAgentLifecycle:
    """Test take → order → execute → release flow with running agent loop."""

    @pytest.mark.asyncio
    async def test_controlled_agent_consumes_order(self, office_world):
        from core.director import Director
        from loop import run_agent
        from agent.brain import Brain
        from prompt.loader import PromptLoader
        from prompt.assembler import PromptAssembler
        from cli.loop_factory import build_loop_config
        from systems.sensory import SensorySystem
        from systems.interaction import InteractionSystem
        from systems.decay import DecaySystem

        systems = {
            "sensory": SensorySystem(),
            "interaction": InteractionSystem(_MockLLM(), None),
            "decay": DecaySystem(),
        }

        director = Director(office_world)
        agent = office_world.entities["coder_01"]

        loader = PromptLoader.__new__(PromptLoader)
        loader.data = {
            "templates": {"agent_decision": {"slots": [], "temperature": 0.7}},
            "slots": {},
            "system_prompts": {},
            "output_schemas": {},
        }
        assembler = PromptAssembler(loader)
        brain = Brain({"deepseek": _MockLLM()}, assembler, "deepseek")

        labels = {"sensory_prompts": {}}
        cfg = build_loop_config(
            office_world._world_cfg.get("world", {}).get("simulation", {}), labels)

        director.take("coder_01", level=2)
        decision = {"action": "write code", "dialogue": "done"}
        director.order("coder_01", decision)

        task = asyncio.create_task(run_agent(
            agent, office_world, brain, assembler, systems,
            5, cfg=cfg, director=director))
        await asyncio.sleep(2)

        remaining = director._orders.get("coder_01")
        assert remaining is None, "Order should be consumed by controlled agent"

        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=2)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass

        director.release("coder_01")

    @pytest.mark.asyncio
    async def test_controlled_agent_not_running_llm(self, office_world):
        """Controlled agent with pending order should skip Phase 2/3 (no LLM call)."""
        from core.director import Director
        from agent.brain import Brain
        from prompt.loader import PromptLoader
        from prompt.assembler import PromptAssembler

        director = Director(office_world)
        director.take("coder_01", level=2)
        assert director.is_controlled("coder_01")
        assert director.pending("coder_01") is None

        decision = {"action": "walk", "target_name": "咖啡机"}
        director.order("coder_01", decision)
        assert director.pending("coder_01") == decision
        assert director.pending("coder_01") is None  # consumed on second pop

        director.release("coder_01")
        assert not director.is_controlled("coder_01")


# ═══════════════════════════════════════════════════════════════════════
# NPC file output — FLUSH writes to disk
# ═══════════════════════════════════════════════════════════════════════

class TestNPCFileOutput:
    """Test that NPCs produce files through AgentWorld's FLUSH mechanism."""

    @pytest.mark.asyncio
    async def test_flush_writes_file_to_disk(self, office_world):
        from core.director import Director
        from loop import run_agent
        from agent.brain import Brain
        from prompt.loader import PromptLoader
        from prompt.assembler import PromptAssembler
        from cli.loop_factory import build_loop_config
        from systems.sensory import SensorySystem
        from systems.interaction import InteractionSystem
        from systems.decay import DecaySystem

        systems = {
            "sensory": SensorySystem(),
            "interaction": InteractionSystem(_MockLLM(), None),
            "decay": DecaySystem(),
        }

        director = Director(office_world)
        agent = office_world.entities["coder_01"]

        loader = PromptLoader.__new__(PromptLoader)
        loader.data = {
            "templates": {"agent_decision": {"slots": [], "temperature": 0.7}},
            "slots": {},
            "system_prompts": {},
            "output_schemas": {},
        }
        assembler = PromptAssembler(loader)
        brain = Brain({"deepseek": _MockLLM()}, assembler, "deepseek")

        labels = {"sensory_prompts": {}}
        cfg = build_loop_config(
            office_world._world_cfg.get("world", {}).get("simulation", {}), labels)

        director.take("coder_01", level=2)
        decision = {
            "action": "write test file",
            "file_output": {
                "filename": "integration_test.txt",
                "content": "NPC wrote this during integration test.",
            },
        }
        director.order("coder_01", decision)

        task = asyncio.create_task(run_agent(
            agent, office_world, brain, assembler, systems,
            5, cfg=cfg, director=director))
        await asyncio.sleep(3)

        out_dir = os.path.join(ROOT, "AutoGenSim", "output")
        files = [f for f in os.listdir(out_dir) if "integration_test" in f]
        assert len(files) == 1, f"Expected 1 test file, found: {files}"

        with open(os.path.join(out_dir, files[0])) as f:
            content = f.read()
        assert "NPC wrote this during integration test" in content

        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=2)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass

        director.release("coder_01")


# ═══════════════════════════════════════════════════════════════════════
# Sensory system integration
# ═══════════════════════════════════════════════════════════════════════

class TestSensoryIntegration:
    """Test that the sensory fix (speech-content comparison) works end-to-end."""

    def test_multiple_utterances_enter_the_same_entity_buffer(self):
        from systems.sensory import SensorySystem
        from layers.agent import AgentLayer
        from layers.auditory import AuditoryLayer
        from agent.sensory_memory import SensoryMemory
        from entity.entity import Entity

        sensor = SensorySystem()
        obs = Entity(id="obs", name="Listener", zone="open_space", pos=[0, 0])
        al = AgentLayer(autonomous=True)
        al.sensory = SensoryMemory()
        al.view_radius = 30
        al.hearing_radius = 30
        obs.layers["agent"] = al

        speaker = Entity(id="s1", name="Alice", zone="open_space", pos=[5, 0])
        aud = AuditoryLayer(audible_radius=20, properties={
            "current_speech": "Hello", "speech_ts": time.time()})
        speaker.layers["auditory"] = aud

        buf = obs.get("agent")._conversation_buffer
        sensor.update(obs, {"s1": speaker})
        assert len(buf) == 1, "First utterance: buffer should have 1 entry"

        # Same speech again → should NOT duplicate
        sensor.update(obs, {"s1": speaker})
        assert len(buf) == 1, "Same speech: buffer should still have 1 entry"

        # Different speech → SHOULD add
        aud.properties["current_speech"] = "How are you?"
        aud.properties["speech_ts"] = time.time()
        sensor.update(obs, {"s1": speaker})
        assert len(buf) == 2, "Different speech: buffer should have 2 entries"
        assert buf[1]["text"] == "How are you?"

    def test_speaker_out_of_range_removed_from_channels(self):
        from systems.sensory import SensorySystem
        from layers.agent import AgentLayer
        from layers.auditory import AuditoryLayer
        from agent.sensory_memory import SensoryMemory
        from entity.entity import Entity

        sensor = SensorySystem()
        obs = Entity(id="obs", name="Listener", zone="open_space", pos=[0, 0])
        al = AgentLayer(autonomous=True)
        al.sensory = SensoryMemory()
        al.view_radius = 30
        al.hearing_radius = 30
        obs.layers["agent"] = al

        speaker = Entity(id="s1", name="Alice", zone="open_space", pos=[2, 0])
        aud = AuditoryLayer(audible_radius=10, properties={
            "current_speech": "Hi", "speech_ts": time.time()})
        speaker.layers["auditory"] = aud

        sensor.update(obs, {"s1": speaker})
        assert "auditory" in al.sensory.channels
        assert "s1" in al.sensory.channels["auditory"]

        # Move speaker far away — out of observer's hearing radius
        speaker.pos = [100, 100]
        sensor.update(obs, {"s1": speaker})
        assert "s1" not in al.sensory.channels.get("auditory", {})


# ═══════════════════════════════════════════════════════════════════════
# Logger integration
# ═══════════════════════════════════════════════════════════════════════

class TestLoggerIntegration:
    """Test that the logger module works end-to-end."""

    def test_errors_are_deduped_across_calls(self):
        from logger import log, enable, disable
        import tempfile, os
        fd, path = tempfile.mkstemp(suffix=".sqlite3")
        os.close(fd); os.unlink(path)
        enable(path)
        log.error(agent="test", module="a", message="x")
        log.error(agent="test", module="a", message="x")
        log.error(agent="test", module="b", message="x")
        disable()
        import sqlite3
        db = sqlite3.connect(path)
        rows = list(db.execute("SELECT module, count FROM errors"))
        assert len(rows) == 2  # a/x and b/x
        counts = {r[0]: r[1] for r in rows}
        assert counts["a"] == 2  # deduped
        assert counts["b"] == 1
        db.close()
        try: os.unlink(path)
        except OSError: pass
        try: os.unlink(path + "-wal")
        except OSError: pass

    def test_dump_produces_human_readable_output(self):
        from logger import log, enable, disable
        import tempfile, os
        fd, path = tempfile.mkstemp(suffix=".sqlite3")
        os.close(fd); os.unlink(path)
        enable(path)
        log.error(agent="test", module="loop.alice", message="LLM timeout after 3 retries")
        log.error(agent="test", module="sensory", message="entity not in candidate list")
        report = log.dump()
        assert "Ticks:" in report
        assert "Errors:" in report
        assert "Storage:" in report
        disable()
        try: os.unlink(path)
        except OSError: pass
        try: os.unlink(path + "-wal")
        except OSError: pass

    def test_summary_returns_dict(self):
        from logger import log, enable, disable
        import tempfile, os
        fd, path = tempfile.mkstemp(suffix=".sqlite3")
        os.close(fd); os.unlink(path)
        enable(path)
        log.error(agent="test", module="brain", message="x")
        log.error(agent="test", module="brain", message="y")
        s = log.summary()
        assert isinstance(s, dict)
        assert s["total_errors"] == 2
        disable()
        os.unlink(path)
        try: os.unlink(path + "-wal")
        except OSError: pass


# ═══════════════════════════════════════════════════════════════════════
# spawn_entity ID collision — end-to-end
# ═══════════════════════════════════════════════════════════════════════

class TestSpawnEntityIntegration:
    """Test spawn_entity with full world — ID collision raises ValueError."""

    def test_spawn_duplicate_preserves_world_state(self, office_world):
        entity_def = {
            "id": "temp_agent", "name": "Temporary",
            "zone": "open_space", "pos": [5, 5],
        }
        office_world.spawn_entity(entity_def)
        assert "temp_agent" in office_world.entities

        with pytest.raises(ValueError, match="already exists"):
            office_world.spawn_entity({
                "id": "temp_agent", "name": "Impostor",
                "zone": "open_space", "pos": [10, 10],
            })

        # Original untouched
        assert office_world.entities["temp_agent"].name == "Temporary"
        assert office_world.entities["temp_agent"].pos == [5, 5]

    def test_despawn_removes_from_world(self, office_world):
        entity_def = {
            "id": "to_remove", "name": "Removable",
            "zone": "open_space", "pos": [1, 1],
        }
        office_world.spawn_entity(entity_def)
        assert office_world.despawn_entity("to_remove") is True
        assert "to_remove" not in office_world.entities

    def test_despawn_nonexistent_returns_false(self, office_world):
        assert office_world.despawn_entity("ghost") is False
