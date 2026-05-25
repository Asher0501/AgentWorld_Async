"""Visual server — thin wrapper around shared frontend infrastructure."""
import os
from src.frontend_shared.server import start_server

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


async def start_visual(emitter, director, port=8767):
    await start_server(emitter, director, STATIC_DIR, port, "Visual")
