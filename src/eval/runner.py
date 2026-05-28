"""Evaluation runner. Reads logger SQLite, runs all registered metrics."""

from .registry import REGISTRY
from .report import EvalReport


def _traces_from_db(db_path: str) -> list[dict]:
    """Convert logger SQLite ticks (result phase) to eval-compatible trace dicts."""
    import sqlite3
    import json
    db = sqlite3.connect(db_path)
    rows = db.execute("""
        SELECT agent, d_action, d_target, d_target_id, d_intent,
               r_narrative, r_deltas, r_thread_done,
               g_drives, g_triggered, g_zone, g_pos_x, g_pos_y,
               g_coins, sim_time, d_llm_output, tick_n
        FROM ticks WHERE phase='result'
        ORDER BY id
    """)
    traces = []
    for r in rows:
        agent, action, target, target_id, intent, narrative, deltas_s, thread_done, \
            drives_s, triggered, zone, pos_x, pos_y, coins, sim, llm_s, tick_n = r
        t = {
            "agent": agent,
            "action_text": action,
            "target": target,
            "target_id": target_id,
            "intent": intent,
            "result_narrative": narrative,
            "result_caller_deltas": json.loads(deltas_s) if deltas_s else {},
            "thread_completed": bool(thread_done),
            "drives": json.loads(drives_s) if drives_s else {},
            "zone": zone,
            "pos": [pos_x, pos_y] if pos_x and pos_y else [0, 0],
            "coins": coins or 0,
            "sim_time": sim or 0,
            "ts": tick_n or 0,
        }
        if llm_s:
            t["llm1_output"] = json.loads(llm_s)
        traces.append(t)
    db.close()
    return traces


def run_eval(source: str) -> EvalReport:
    """Read traces from logger SQLite (or JSON fallback) and run metrics."""
    import os
    if source.endswith(".sqlite3") or source.endswith(".db"):
        traces = _traces_from_db(source)
    else:
        import json
        with open(source) as f:
            traces: list[dict] = json.load(f)

    # Extract _meta if embedded
    meta = {}
    if traces and isinstance(traces[0], dict) and traces[0].get("_meta"):
        meta = traces.pop(0)["_meta"]

    actions = [t for t in traces if t.get("action_text")]
    agents = sorted(set(t["agent"] for t in traces))

    results: dict[str, dict] = {}
    errors: dict[str, str] = {}
    for name, m in REGISTRY.items():
        try:
            fn = m["fn"]
            import inspect
            sig = inspect.signature(fn)
            if len(sig.parameters) > 1 and meta:
                results[name] = {
                    "value": fn(traces, meta),
                    "category": m["category"],
                    "description": m["description"],
                    "source": m["source"],
                }
            else:
                results[name] = {
                    "value": fn(traces),
                    "category": m["category"],
                    "description": m["description"],
                    "source": m["source"],
                }
        except Exception as e:
            errors[name] = f"{type(e).__name__}: {e}"

    return EvalReport(
        trace_path=source,
        n_traces=len(traces),
        n_actions=len(actions),
        n_agents=len(agents),
        agents=agents,
        results=results,
        errors=errors,
    )
