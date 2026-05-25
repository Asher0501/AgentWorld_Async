"""Dashboard server — thin wrapper around shared frontend infrastructure."""
import os
from src.frontend_shared.server import start_server

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


async def start_dashboard(emitter, director, port=8766):
    await start_server(emitter, director, STATIC_DIR, port, "Dashboard")
