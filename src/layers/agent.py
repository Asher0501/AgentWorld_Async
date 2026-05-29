from dataclasses import dataclass, field
from layers.base import Layer


@dataclass
class AgentLayer(Layer):
    autonomous: bool = False
    speed: float = 1.0
    view_radius: int = 20
    hearing_radius: int = 15
    interaction_radius: int = 3
    personality: str = ""
    main_thread: str = ""
    template: str = ""   # override agent_decision template per-agent (YAML configurable)
    llm_provider: str = ""  # provider key for multi-LLM routing (YAML configurable)

    # Runtime modules
    drives: object = None
    sensory: object = None
    memory: object = None

    # ── KL snapshot (P-distribution) ──
    p_channels: dict = field(default_factory=dict)
    p_state:    dict = field(default_factory=dict)
    p_stale:    float = 0.0

    # ── Write-pending lock ──
    _write_pending: bool = False

    # ── Action pacing ──
    _action_complete_at: float = 0.0  # wall-clock timestamp; while now < this, skip decide
    _pending_action: tuple = None     # (decision, target_entity) — enqueued, flushes on expiry

    # ── Slot groups ──
    slot_mask: dict = field(default_factory=dict)  # merged world+npc+contract mask {slot_name: 0/1}
    traits: list = field(default_factory=list)     # trait names from world.yaml

    # ── Conversation state (factual — LLM decides what to do with it) ──
    _last_target_name: str = ""
    _pending_narrative: str = ""
    _conversation_buffer: list = field(default_factory=list)

    # ── Intent tracking ──
    _last_intent: str = ""
