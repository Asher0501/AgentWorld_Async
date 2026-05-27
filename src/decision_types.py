"""Type contracts for AgentWorld decision pipeline. No runtime impact — IDE support only."""
from typing import TypedDict, Optional, NotRequired


class FileOutput(TypedDict, total=False):
    filename: str
    content: str


class DecisionDict(TypedDict, total=False):
    """The JSON decision a Brain returns / a Director orders.
    All fields optional — LLM fills what's relevant."""
    action: str
    target_name: NotRequired[str]
    dialogue: NotRequired[str]
    duration: NotRequired[float]
    expects_reply: NotRequired[bool]
    intent: NotRequired[str]
    main_thread: NotRequired[str]
    main_thread_reason: NotRequired[str]
    main_thread_update: NotRequired[str]
    thread_completed: NotRequired[bool]
    thinking: NotRequired[str]
    internal: NotRequired[str]
    file_output: NotRequired[FileOutput]
    story: NotRequired[str]
    visual: NotRequired[str]
    self_deltas: NotRequired[dict]
