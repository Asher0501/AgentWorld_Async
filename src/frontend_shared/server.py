"""Frontend shared — generic aiohttp server for Dashboard and Visual modules."""
import asyncio
import os
from aiohttp import web


async def _ws_handler(request):
    emitter = request.app["emitter"]
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    q = await emitter.register()
    stream_task = asyncio.create_task(_stream_events(emitter, ws, q))
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.ERROR:
                break
    finally:
        emitter.unregister(q)
        stream_task.cancel()
        try:
            await stream_task
        except asyncio.CancelledError:
            pass
        await ws.close()
    return ws


async def _stream_events(emitter, ws, q):
    try:
        while True:
            payload = await q.get()
            await ws.send_str(payload)
    except asyncio.CancelledError:
        pass
    except Exception:
        pass


async def start_server(emitter, director, static_dir, port, name):
    """Start a generic aiohttp HTTP + WebSocket server."""
    from .director_api import register_director_routes
    app = web.Application()
    app["emitter"] = emitter
    app.router.add_get("/", lambda r: web.FileResponse(os.path.join(static_dir, "index.html")))
    app.router.add_get("/ws", _ws_handler)
    register_director_routes(app, director)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    from logger import log
    log.info(agent="server", module="frontend",
             message=f"{name} listening on port {port}")
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        await runner.cleanup()
