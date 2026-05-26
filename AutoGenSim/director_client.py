"""Director HTTP client — zero dependency on AgentWorld internals."""
import aiohttp


class DirectorClient:
    """Thin HTTP wrapper around AgentWorld's Director REST API."""

    def __init__(self, base_url: str = "http://localhost:8766"):
        self.base_url = base_url

    async def _api(self, method: str, path: str, body: dict = None) -> dict:
        async with aiohttp.ClientSession() as s:
            kwargs = {}
            if body:
                kwargs["json"] = body
            async with s.request(method, f"{self.base_url}{path}", **kwargs) as r:
                return await r.json()

    async def state(self) -> dict:
        return await self._api("GET", "/api/state")

    async def freeze(self) -> dict:
        return await self._api("POST", "/api/freeze")

    async def unfreeze(self) -> dict:
        return await self._api("POST", "/api/unfreeze")

    async def take(self, agent_id: str, level: int = 1) -> dict:
        return await self._api("POST", f"/api/take/{agent_id}", {"level": level})

    async def release(self, agent_id: str) -> dict:
        return await self._api("POST", f"/api/release/{agent_id}")

    async def snap(self, agent_id: str) -> dict:
        return await self._api("GET", f"/api/snap/{agent_id}")

    async def order(self, agent_id: str, decision: dict) -> dict:
        return await self._api("POST", f"/api/order/{agent_id}", {"decision": decision})

    async def set(self, agent_id: str, path: str, value) -> dict:
        return await self._api("POST", f"/api/set/{agent_id}", {"path": path, "value": value})

    async def memorize(self, agent_id: str, text: str) -> dict:
        return await self._api("POST", f"/api/memorize/{agent_id}", {"text": text})
