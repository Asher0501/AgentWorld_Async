"""Director REST API — shared between Dashboard and Visual frontends."""
from aiohttp import web


def register_director_routes(app: web.Application, director):
    """Attach Director endpoints to the aiohttp app."""

    async def _state(request):
        return web.json_response({"frozen": director.frozen, "controlled": sorted(director._controlled), "pending": {k: v for k, v in director._orders.items()}})

    async def _freeze(request):
        director.freeze()
        return web.json_response({"status": "ok", "frozen": True})

    async def _unfreeze(request):
        director.unfreeze()
        return web.json_response({"status": "ok", "frozen": False})

    async def _take(request):
        director.take(request.match_info["agent_id"])
        return web.json_response({"status": "ok", "controlled": True})

    async def _release(request):
        director.release(request.match_info["agent_id"])
        return web.json_response({"status": "ok", "controlled": False})

    async def _snap(request):
        data = director.snap(request.match_info["agent_id"])
        if "sensory" in data and data["sensory"]:
            clean = {}
            for ch, ch_data in data["sensory"].items():
                clean[ch] = {eid: {"name": r.name, "distance": r.distance, "data": r.data} for eid, r in (ch_data or {}).items()}
            data["sensory"] = clean
        return web.json_response(data)

    async def _order(request):
        body = await request.json()
        director.order(request.match_info["agent_id"], body.get("decision", {}))
        return web.json_response({"status": "ok"})

    app.router.add_get("/api/state", _state)
    app.router.add_post("/api/freeze", _freeze)
    app.router.add_post("/api/unfreeze", _unfreeze)
    app.router.add_post("/api/take/{agent_id}", _take)
    app.router.add_post("/api/release/{agent_id}", _release)
    app.router.add_get("/api/snap/{agent_id}", _snap)
    app.router.add_post("/api/order/{agent_id}", _order)
