"""Concurrent agent execution."""
import asyncio
from loop import run_agent


async def run_concurrent(agents, world, brain, assembler, systems,
                         runtime: float, cfg,
                         *, director=None,
                         dashboard_emit=None):
    """Run all agents concurrently."""
    tasks = [run_agent(a, world, brain, assembler, systems,
                        runtime, cfg=cfg,
                        director=director, dashboard_emit=dashboard_emit)
             for a in agents]
    await asyncio.gather(*tasks, return_exceptions=True)
