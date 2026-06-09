"""Minimal director client for integration tests."""
import aiohttp
import asyncio
import json


class DirectorClient:
    def __init__(self, base_url="http://localhost:8765"):
        self.base_url = base_url.rstrip("/")

    async def _get(self, path):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}{path}") as resp:
                return await resp.json()

    async def _post(self, path, data=None):
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}{path}", json=data or {}) as resp:
                return await resp.json()

    async def state(self):
        return await self._get("/state")

    async def snap(self, agent_id):
        return await self._get(f"/snap/{agent_id}")

    async def take(self, agent_id, level="write"):
        return await self._post(f"/take/{agent_id}", {"level": level})

    async def release(self, agent_id):
        return await self._post(f"/release/{agent_id}")

    async def order(self, agent_id, decision):
        return await self._post(f"/order/{agent_id}", {"decision": decision})

    async def set(self, agent_id, path, value):
        return await self._post(f"/set/{agent_id}", {"path": path, "value": value})

    async def memorize(self, agent_id, text):
        return await self._post(f"/memorize/{agent_id}", {"text": text})
