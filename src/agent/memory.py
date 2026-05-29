import time
from dataclasses import dataclass, field


@dataclass
class AgentMemory:
    entries: list[dict] = field(default_factory=list)  # [{ts, text}]
    max_size: int = 10
    evicted_count: int = 0  # how many entries have been silently pruned

    def record(self, text: str = "", ts: float = None) -> None:
        self.entries.append({
            "ts": ts if ts is not None else time.time(),
            "text": text,
        })
        non_pinned = [e for e in self.entries if not e.get("pinned")]
        while len(non_pinned) > self.max_size:
            idx = self.entries.index(non_pinned[0])
            self.entries.pop(idx)
            non_pinned.pop(0)
            self.evicted_count += 1

    def recent(self, n: int = 5) -> list[dict]:
        return self.entries[-n:]

    def to_prompt_text(self, n: int = 5, labels: dict = None) -> str:
        if not labels:
            return ""
        entries = self.recent(n)
        if not entries:
            return labels["empty_memory"]
        lines = []
        ref_ts = entries[0]["ts"]
        for e in entries:
            rel = int(e["ts"] - ref_ts)
            lines.append(labels["memory_entry"].format(rel=rel, text=e['text']))
        if self.evicted_count:
            evicted_tpl = labels.get("memory_evicted", "")
            if evicted_tpl:
                lines.append(evicted_tpl.format(
                    seconds=int(time.time() - entries[-1]['ts']),
                    evicted_count=self.evicted_count))
        return "\n".join(lines)

    def latest(self) -> dict | None:
        return self.entries[-1] if self.entries else None
